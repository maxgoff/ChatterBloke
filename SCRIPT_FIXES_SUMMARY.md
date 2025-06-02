# Script Management Fixes Summary

## Issues Fixed

### 1. Script Save Error (500 Error)
**Problem**: PUT /api/scripts was failing because only content was being sent, not title.
**Fix**: Modified `save_script()` to include both title and content in the update request.

### 2. Import Script Functionality
**Problem**: No way to import scripts from text files into the database.
**Fix**: Enhanced `open_script()` to:
- Read text file content
- Ask user if they want to import to database
- Create new script in database if yes
- Just load locally if no

### 3. Export Script Functionality
**Problem**: No way to export scripts to text files.
**Fix**: Added:
- Export button in toolbar
- `export_script()` method to save current script to file
- Clean filename generation from script title

### 4. Scripts Not Appearing in Teleprompter
**Problem**: Teleprompter didn't refresh when new scripts were created.
**Fix**: Added `showEvent()` to Teleprompter tab to reload scripts when tab becomes visible.

### 5. Script Management Features
**Problem**: Limited script management options.
**Fix**: Added context menu (right-click) on script list with:
- **Rename**: Change script title
- **Duplicate**: Create a copy of script
- **Export**: Save specific script to file
- **Delete**: Remove script with confirmation

## New Features

### Context Menu Operations
Right-click any script in the list to:
- Rename script
- Duplicate script (creates "Title (Copy)")
- Export to file
- Delete script

### Import/Export Workflow
1. **Import**: Open → Select text file → Choose to import to database
2. **Export**: Current script → Export button → Save as text file
3. **Export Any**: Right-click script → Export to File

### Auto-refresh
- Teleprompter tab now refreshes scripts when opened
- Script Editor updates list after all operations

## Usage

### Import a Script
1. Click "Open" or press Ctrl+O
2. Select a text file
3. Choose "Yes" to import to database
4. Script is created and loaded

### Export Current Script
1. Click "Export" button in toolbar
2. Choose filename and location
3. Script is saved as text file

### Manage Scripts
1. Right-click any script in the list
2. Choose desired operation
3. Follow prompts

### Fix for Teleprompter
- Scripts now appear immediately in Teleprompter
- Switch to Teleprompter tab to see updated list
- Use reload button (↻) to manually refresh