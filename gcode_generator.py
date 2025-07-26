import re
import json
import os
from PySide6.QtCore import QObject, Signal
from datetime import datetime


class GCodeGenerator(QObject):
    """Core G-code generation engine with real-time updates"""
    
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
        
        # Load types data on startup
        self.load_types_data()
    
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
        """Generate individual file content"""
        # Get base G-code template
        base_gcode = ""
        
        if file_type == 'frame':
            if side == 'left' and self.profiles['left_frame']:
                base_gcode = self.profiles['left_frame']
            elif side == 'right' and self.profiles['right_frame']:
                base_gcode = self.profiles['right_frame']
            else:
                return ""
        elif file_type == 'lock':
            base_gcode = self._get_profile_gcode(self.profiles['lock'])
        elif file_type == 'hinge':
            base_gcode = self._get_profile_gcode(self.profiles['hinge'])
        
        if not base_gcode:
            return ""
        
        # Prepare substitution values
        substitution_values = self._prepare_substitution_values(side, file_type)
        
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
        
        # Frame configuration values
        if self.frame_config:
            values.update({
                'frame_height': str(self.frame_config.get('height', 0)),
                'frame_width': str(self.frame_config.get('width', 1200)),
                'machine_x_offset': str(self.frame_config.get('x_offset', 0)),
                'machine_y_offset': str(self.frame_config.get('y_offset', 0)),
                'machine_z_offset': str(self.frame_config.get('z_offset', 0)),
                'lock_position': str(self.frame_config.get('lock_position', 0)),
                'lock_y_offset': str(self.frame_config.get('lock_y_offset', 0)),
                'hinge_y_offset': str(self.frame_config.get('hinge_y_offset', 0)),
                'orientation': self.frame_config.get('orientation', 'right')
            })
            
            # PM positions
            pm_positions = self.frame_config.get('pm_positions', [])
            for i, pos in enumerate(pm_positions):
                values[f'pm{i+1}_position'] = str(pos)
            
            # Hinge positions
            hinge_positions = self.frame_config.get('hinge_positions', [])
            for i, pos in enumerate(hinge_positions):
                values[f'hinge{i+1}_position'] = str(pos)
        
        # Side-specific adjustments
        if side == 'left':
            # Apply left-side specific transformations
            values['side_multiplier'] = '-1'  # For X coordinates
            values['side_offset'] = '0'
        else:  # right
            values['side_multiplier'] = '1'
            values['side_offset'] = '0'
        
        # Profile-specific variables
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
        """Perform variable substitution in G-code"""
        result = gcode
        
        # Find all variables in format {variable} or {variable:default}
        pattern = r'\{([^}:]+)(?::([^}]*))?\}'
        
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