# CNC Frame Wizard - Project Overview

## 🎯 Project Description

A desktop wizard application that generates G-code files for CNC machines to manufacture door/window frames. The app uses pre-defined templates and allows users to customize variables for different hinge and lock profiles, making the G-code generation process quick and user-friendly.

## 🖼️ UI Layout & Flow

### Tab 1: Profile Selection
```
┌─────────────────────────────────────────────────────────────┐
│  [Profile Selection] | [Frame Setup] | [Generate Files]      │
├─────────────────────────────────────────────────────────────┤
│  ┌─── Hinges ───────────────┐  ┌─── Locks ────────────────┐ │
│  │ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │  │ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │ │
│  │ │ + │ │📁│ │📁│ │📁│ │  │ │ + │ │🔒│ │🔒│ │🔒│ │ │
│  │ └───┘ └───┘ └───┘ └───┘ │  │ └───┘ └───┘ └───┘ └───┘ │ │
│  │  New   H-01  H-02  H-03  │  │  New   L-01  L-02  L-03  │ │
│  │                          │  │                          │ │
│  │ (Scrollable Grid View)   │  │ (Scrollable Grid View)   │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                                              │
│  Selected: [Hinge: H-01] [Lock: L-02]          [Next →]    │
└─────────────────────────────────────────────────────────────┘
```

### Profile Editor Window (Modal)
```
┌─── Edit Profile: H-01 ─────────────────────────────────────┐
│  Profile Type: [Hinge Type A ▼]                            │
│                                                            │
│  ┌─── Variables ────────┐  ┌─── Preview ────────────────┐ │
│  │ Width:    [45.5]     │  │    ┌─────────────┐         │ │
│  │ Height:   [120.0]    │  │    │   Drawing   │         │ │
│  │ Depth:    [15.0]     │  │    │   showing   │         │ │
│  │ Offset:   [2.5]      │  │    │ dimensions  │         │ │
│  │ Radius:   [5.0]      │  │    └─────────────┘         │ │
│  └──────────────────────┘  └─────────────────────────────┘ │
│                                                            │
│                         [Cancel] [Confirm]                 │
└────────────────────────────────────────────────────────────┘
```

### Tab 2: Frame Setup
```
┌─────────────────────────────────────────────────────────────┐
│  [Profile Selection] | [Frame Setup] | [Generate Files]      │
├─────────────────────────────────────────────────────────────┤
│  ┌─── Frame Dimensions ─────┐  ┌─── Visual Guide ─────────┐ │
│  │ Width:  [1200.0] mm      │  │  ┌─────────────────┐     │ │
│  │ Height: [2100.0] mm      │  │  │                 │     │ │
│  │                          │  │  │   Frame         │     │ │
│  └──────────────────────────┘  │  │   Diagram       │     │ │
│                                 │  │                 │     │ │
│  ┌─── Hinge Configuration ──┐  │  └─────────────────┘     │ │
│  │ Number of Hinges: [3 ▼]  │  └──────────────────────────┘ │
│  │ □ Auto-position          │                               │
│  │ Position 1: [350.0] mm   │  ┌─── Lock Configuration ───┐ │
│  │ Position 2: [1050.0] mm  │  │ Position: [1050.0] mm     │ │
│  │ Position 3: [1750.0] mm  │  └──────────────────────────┘ │
│  │                          │                               │
│  │ Y Alignment: [Center ▼]  │  ┌─── Frame Options ────────┐ │
│  │ Z Alignment: [Front ▼]   │  │ □ Mirror for right side   │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                                              │
│                                    [← Back] [Next →]         │
└─────────────────────────────────────────────────────────────┘
```

### Tab 3: Generate Files
```
┌─────────────────────────────────────────────────────────────┐
│  [Profile Selection] | [Frame Setup] | [Generate Files]      │
├─────────────────────────────────────────────────────────────┤
│  Generated G-Code Files:                                     │
│                                                              │
│  ┌─── Left Side ────────────┐  ┌─── Right Side ──────────┐ │
│  │ 📄 frame_left_top.nc     │  │ 📄 frame_right_top.nc    │ │
│  │ 📄 frame_left_side.nc    │  │ 📄 frame_right_side.nc   │ │
│  │ 📄 frame_left_bottom.nc  │  │ 📄 frame_right_bottom.nc │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                                              │
│  Output Directory: [C:/CNC/Output/]              [Browse]    │
│                                                              │
│                              [← Back] [Generate Files]       │
└─────────────────────────────────────────────────────────────┘
```

### File Preview Window (Modal)
```
┌─── Preview: frame_left_top.nc ──────────────────────────────┐
│  ┌─── G-Code ───────────────┐  ┌─── Toolpath Preview ─────┐ │
│  │ ; Frame Left Top         │  │  ┌──────────────────┐    │ │
│  │ ; Generated: 2024-01-15  │  │  │                  │    │ │
│  │ G21 ; mm mode            │  │  │   3D Toolpath    │    │ │
│  │ G90 ; absolute           │  │  │   Visualization  │    │ │
│  │ G0 X0 Y0 Z5              │  │  │                  │    │ │
│  │ G1 Z-5 F100              │  │  └──────────────────┘    │ │
│  │ G1 X45.5 F300            │  │                           │ │
│  │ ...                      │  │  [Reset View] [Zoom]      │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                                              │
│                                               [Close]        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project File Structure

```
cnc-frame-wizard/
│
├── main.py                 # Application entry point & main window setup
├── requirements.txt        # Python dependencies (Pyside6, numpy, etc.)
├── config.json            # Default settings and paths
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Main window with tab widget
│   ├── profile_tab.py     # Tab 1: Profile selection grid views
│   ├── frame_tab.py       # Tab 2: Frame configuration
│   ├── generate_tab.py    # Tab 3: File generation and preview
│   ├── profile_editor.py  # Modal dialog for profile editing
│   └── preview_dialog.py  # Modal dialog for G-code preview
│
├── core/
│   ├── __init__.py
│   ├── profile_manager.py # Load/save/manage hinge & lock profiles
│   ├── gcode_generator.py # Template-based G-code generation logic
│   ├── gcode_preview.py   # Parse G-code for visualization
│   └── models.py          # Data classes for profiles and frames
│
├── widgets/
│   ├── __init__.py
│   ├── profile_grid.py    # Custom widget for profile grid view
│   ├── diagram_viewer.py  # Widget to display dimension diagrams
│   └── toolpath_viewer.py # 3D visualization widget for G-code
│
├── templates/
│   ├── frame_top.nc       # G-code template for top piece
│   ├── frame_side.nc      # G-code template for side piece
│   └── frame_bottom.nc    # G-code template for bottom piece
│
├── resources/
│   ├── profiles/          # JSON files for saved profiles
│   │   ├── hinges/
│   │   └── locks/
│   ├── images/            # UI icons and dimension diagrams
│   └── styles/            # QSS stylesheets
│
└── output/                # Default directory for generated G-code
```

## 📋 File Descriptions

### **main.py**
- Creates QApplication instance
- Loads configuration from config.json
- Initializes and shows MainWindow
- Sets up global exception handling

### **ui/main_window.py**
- QMainWindow subclass with QTabWidget
- Manages navigation between tabs
- Handles tab enable/disable logic based on selection state
- Connects signals between tabs

### **ui/profile_tab.py**
- Contains two ProfileGrid widgets (hinges & locks)
- Manages selected profiles state
- Handles context menu for edit/duplicate/delete
- Opens ProfileEditor dialog when needed

### **ui/frame_tab.py**
- Form layout for frame dimensions
- Dynamic hinge position inputs based on count
- Auto-position calculation logic
- Lock position configuration
- Diagram display for visual reference

### **ui/generate_tab.py**
- Displays list of files to be generated
- File preview on click
- Generate button handler
- Output directory selection

### **core/profile_manager.py**
- Load profiles from JSON files
- Save new/edited profiles
- Handle profile CRUD operations
- Validate profile data

### **core/gcode_generator.py**
- Load G-code templates
- Replace template variables with actual values
- Calculate positions and offsets
- Generate left/right mirror versions

### **widgets/profile_grid.py**
- Custom QWidget showing icons in grid layout
- Drag & drop support for reordering
- Selection highlighting
- Context menu integration
- Responsive layout adjustment

## 🔧 Key Technologies

- **PyQt5**: Main UI framework
- **JSON**: Profile and configuration storage
- **Jinja2**: Template engine for G-code generation
- **NumPy**: Coordinate calculations
- **PyOpenGL** (optional): 3D toolpath visualization

## 💾 Data Flow

1. User selects hinge and lock profiles from saved presets
2. Profile data (dimensions, offsets) loaded into memory
3. User inputs frame dimensions and positions
4. Generator combines frame data with profile data
5. Template engine replaces variables in G-code templates
6. Six files generated (3 left + 3 right pieces)
7. Files saved to output directory

## 🎨 Design Principles

- **Wizard-style navigation**: Linear flow with clear steps
- **Visual feedback**: Diagrams show what each variable controls
- **Template-based**: No complex G-code generation logic
- **Profile reusability**: Save common configurations
- **Preview before generate**: Verify output before saving