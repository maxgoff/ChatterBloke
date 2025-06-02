# Mirror Mode Fix

## Problem
The mirror mode was attempting to use custom painting which created issues with QTextEdit's internal rendering.

## Solution
Changed to use QWidget's transform functionality directly:
- Apply a QTransform with scale(-1, 1) to flip horizontally
- This flips the entire widget including text and scrollbars
- Much simpler and more reliable than custom painting

## How It Works

### Normal Mode
```
THE QUICK BROWN FOX
```

### Mirror Mode (Flipped Horizontally)
```
XOF NWORB KCIUQ EHT
```

## Implementation

```python
def set_mirrored(self, mirrored: bool) -> None:
    """Enable or disable mirror mode."""
    self.is_mirrored = mirrored
    
    if mirrored:
        # Apply horizontal flip transformation
        transform = QTransform()
        # Scale horizontally by -1 to flip
        transform.scale(-1, 1)
        self.setTransform(transform)
    else:
        # Reset to original transform
        self.setTransform(self.original_transform)
```

## Use Cases
Mirror mode is used with teleprompter glass (beam splitter) setups where:
1. Text is displayed on a monitor
2. Reflected off angled glass
3. Camera shoots through the glass
4. Presenter reads the reflected text

The text must be mirrored on the monitor so it appears correct when reflected.

## Testing
Run `python test_mirror_mode.py` to see the mirror mode in action.