import re
import json
import os
from PySide6.QtCore import QObject, Signal
from datetime import datetime


class GCodeGenerator(QObject):
    """Enhanced G-code generation engine with $ variable support"""
    
    files_updated = Signal(dict)  # Emits generated files when updated
    
    def __init__(self):
        super().__init__()
        self.frame_config = {}
        self.profiles = {
            'hinge': None,
            'lock': None,
            'left_frame': "",
            'right_frame': ""
        }
        self.types_data = {
            'hinge': {},
            'lock': {}
        }
        self.generated_files = {
            'left': {
                'frame': {'content': '', 'original': ''},
                'lock': {'content': '', 'original': ''},
                'hinge': {'content': '', 'original': ''}
            },
            'right': {
                'frame': {'content': '', 'original': ''},
                'lock': {'content': '', 'original': ''},
                'hinge': {'content': '', 'original': ''}
            }
        }
        
        # Available $ variables with descriptions
        self.dollar_variables_info = {
            # Frame variables
            'frame_height': 'Height of the door frame in mm',
            'frame_width': 'Width of the door frame in mm (fixed at 1200mm)',
            
            # Machine offsets
            'machine_x_offset': 'Machine X axis offset in mm',
            'machine_y_offset': 'Machine Y axis offset in mm', 
            'machine_z_offset': 'Machine Z axis offset in mm',
            
            # PM positions
            'pm1_position': 'Position of PM1 from top of frame in mm',
            'pm2_position': 'Position of PM2 from top of frame in mm',
            'pm3_position': 'Position of PM3 from top of frame in mm',
            'pm4_position': 'Position of PM4 from top of frame in mm',
            
            # Lock configuration
            'lock_position': 'Position of lock from top of frame in mm',
            'lock_y_offset': 'Lock Y-axis offset in mm',
            'lock_active': 'Lock active state (1=active, 0=inactive)',
            'lock_order': 'Lock execution order (0 if inactive)',
            
            # Hinge configuration
            'hinge1_position': 'Position of hinge 1 from top of frame in mm',
            'hinge2_position': 'Position of hinge 2 from top of frame in mm',
            'hinge3_position': 'Position of hinge 3 from top of frame in mm',
            'hinge4_position': 'Position of hinge 4 from top of frame in mm',
            'hinge1_active': 'Hinge 1 active state (1=active, 0=inactive)',
            'hinge2_active': 'Hinge 2 active state (1=active, 0=inactive)',
            'hinge3_active': 'Hinge 3 active state (1=active, 0=inactive)',
            'hinge4_active': 'Hinge 4 active state (1=active, 0=inactive)',
            'hinge1_order': 'Hinge 1 execution order (0 if inactive)',
            'hinge2_order': 'Hinge 2 execution order (0 if inactive)', 
            'hinge3_order': 'Hinge 3 execution order (0 if inactive)',
            'hinge4_order': 'Hinge 4 execution order (0 if inactive)',
            'hinge_y_offset': 'Global hinge Y-axis offset in mm',
            
            # Door orientation
            'orientation': 'Door orientation ("left" or "right")',
        }
        
        # Load types data on startup
        self.load_types_data()
    
    def get_dollar_variables_info(self):
        """Get dictionary of available $ variables with descriptions"""
        return self.dollar_variables_info.copy()
    
    def load_types_data(self):
        """Load types data from profiles/current.json"""
        try:
            current_file = os.path.join("profiles", "current.json")
            if os.path.exists(current_file):
                with open(current_file, 'r') as f:
                    data = json.load(f)
                
                self.types_data['hinge'] = data.get('hinges', {}).get('types', {})
                self.types_data['lock'] = data.get('locks', {}).get('types', {})
        except Exception as e:
            print(f"Error loading types data: {str(e)}")
    
    def update_frame_config(self, config):
        """Update frame configuration and regenerate files"""
        self.frame_config = config.copy()
        self.regenerate_all()
    
    def update_profiles(self, hinge_profile, lock_profile, left_frame="", right_frame=""):
        """Update selected profiles and regenerate files"""
        self.profiles['hinge'] = hinge_profile
        self.profiles['lock'] = lock_profile
        self.profiles['left_frame'] = left_frame
        self.profiles['right_frame'] = right_frame
        self.regenerate_all()
    
    def regenerate_all(self):
        """Regenerate all 6 files and emit update signal"""
        if not self._has_required_data():
            return
        
        # Generate all files
        for side in ['left', 'right']:
            for file_type in ['frame', 'lock', 'hinge']:
                content = self._generate_file(side, file_type)
                
                # Update original content (auto-generated)
                self.generated_files[side][file_type]['original'] = content
                
                # Update current content only if not manually modified
                current = self.generated_files[side][file_type]['content']
                previous_original = self.generated_files[side][file_type].get('previous_original', '')
                
                if not current or current == previous_original:
                    self.generated_files[side][file_type]['content'] = content
                
                # Store previous original for comparison
                self.generated_files[side][file_type]['previous_original'] = content
        
        self.files_updated.emit(self.generated_files)
    
    def _has_required_data(self):
        """Check if we have all required data for generation"""
        return (
            self.frame_config and 
            self.profiles['hinge'] and 
            self.profiles['lock']
        )
    
    def _generate_file(self, side, file_type):
        """Generate individual file content with $ variable substitution"""
        # Get base G-code template
        base_gcode = ""
        
        if file_type == 'frame':
            # Use frame G-code from profile_data (edited from frame tab)
            profile_data = self.frame_config.get('profile_data', {})
            hinge_data = profile_data.get('hinge', {})
            
            if side == 'left':
                base_gcode = hinge_data.get('gcode_left', '')
            else:  # right
                base_gcode = hinge_data.get('gcode_right', '')
                
        elif file_type == 'lock':
            base_gcode = self._get_profile_gcode(self.profiles['lock'])
        elif file_type == 'hinge':
            base_gcode = self._get_profile_gcode(self.profiles['hinge'])
        
        if not base_gcode:
            return ""
        
        # Get $ variable values from frame configuration
        dollar_values = self.frame_config.get('dollar_variables', {})
        
        # Prepare all substitution values (L variables, custom variables, $ variables)
        substitution_values = self._prepare_substitution_values(side, file_type)
        
        # Add $ variables to substitution values with $ prefix
        for var_name, var_value in dollar_values.items():
            substitution_values[f'${var_name}'] = str(var_value)
        
        # Perform variable substitution
        result = self._substitute_variables(base_gcode, substitution_values)
        
        return result
    
    def _get_profile_gcode(self, profile):
        """Extract G-code from profile data structure"""
        if not profile or 'type' not in profile:
            return ""
        
        type_name = profile['type']
        
        # Get the type data from our loaded types
        if profile == self.profiles['hinge']:
            type_data = self.types_data['hinge'].get(type_name, {})
        elif profile == self.profiles['lock']:
            type_data = self.types_data['lock'].get(type_name, {})
        else:
            return ""
        
        return type_data.get('gcode', '')
    
    def _prepare_substitution_values(self, side, file_type):
        """Prepare all substitution values for a specific file"""
        values = {}
        
        # Profile-specific variables (L-variables and custom variables)
        profile_key = 'lock' if file_type == 'lock' else 'hinge' if file_type == 'hinge' else None
        if profile_key and self.profiles[profile_key]:
            profile = self.profiles[profile_key]
            
            # Add L-variables
            l_vars = profile.get('l_variables', {})
            for var_name, var_value in l_vars.items():
                values[var_name] = str(var_value)
            
            # Add custom variables
            custom_vars = profile.get('custom_variables', {})
            for var_name, var_value in custom_vars.items():
                values[var_name] = str(var_value)
        
        return values
    
    def _substitute_variables(self, gcode, values):
        """Perform variable substitution in G-code (handles both {var} and {$var} patterns)"""
        result = gcode
        
        # Find all variables in format {variable} or {variable:default} including $ variables
        pattern = r'\{(\$?[^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            # Return the substituted value or default
            return values.get(var_name, default_value)
        
        result = re.sub(pattern, replace_var, result)
        
        return result
    
    def update_file_content(self, side, file_type, new_content):
        """Update file content after manual editing"""
        if side in self.generated_files and file_type in self.generated_files[side]:
            self.generated_files[side][file_type]['content'] = new_content
    
    def get_file_content(self, side, file_type):
        """Get current file content"""
        return self.generated_files.get(side, {}).get(file_type, {}).get('content', '')
    
    def is_file_modified(self, side, file_type):
        """Check if file has been manually modified"""
        file_data = self.generated_files.get(side, {}).get(file_type, {})
        current = file_data.get('content', '')
        original = file_data.get('original', '')
        return current != original
    
    def reset_file_to_original(self, side, file_type):
        """Reset file content to auto-generated version"""
        if side in self.generated_files and file_type in self.generated_files[side]:
            original = self.generated_files[side][file_type]['original']
            self.generated_files[side][file_type]['content'] = original
    
    def export_files(self, output_directory):
        """Export all files to directory with Windows line endings"""
        # Create timestamped subdirectory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        project_dir = os.path.join(output_directory, f"CNC_Project_{timestamp}")
        
        try:
            os.makedirs(project_dir, exist_ok=True)
            
            exported_files = []
            
            for side in ['left', 'right']:
                side_dir = os.path.join(project_dir, side)
                os.makedirs(side_dir, exist_ok=True)
                
                for file_type in ['frame', 'lock', 'hinge']:
                    content = self.get_file_content(side, file_type)
                    if content:
                        # Convert line endings to Windows format
                        content_windows = content.replace('\n', '\r\n').replace('\r\r\n', '\r\n')
                        
                        filename = f"{side}_{file_type}.txt"
                        filepath = os.path.join(side_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content_windows)
                        
                        exported_files.append(filepath)
            
            return exported_files, project_dir
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")