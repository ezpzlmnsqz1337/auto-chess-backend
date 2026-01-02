# LED Mode Selection and Piece Placement Features

## Overview

Added LED patterns for game setup phase, including mode selection screens and piece placement feedback.

## New Features

### 1. Mode Selection Screens

Three game modes with distinct LED patterns:

#### AI vs AI Mode
- **Pattern**: Alternating cyan/purple across entire board
- **Colors**: Cyan (0, 150, 150) and Purple (150, 0, 150)
- **Purpose**: Both sides controlled by AI
- **Visual**: Full board animated with AI colors

#### Player vs AI Mode
- **White Side (rows 0-1)**: Warm white/gold (player colors)
  - Warm white: (200, 200, 150)
  - Gold: (180, 150, 50)
- **Black Side (rows 6-7)**: Cyan/purple (AI colors)
  - Cyan: (0, 150, 150)
  - Purple: (150, 0, 150)
- **Purpose**: Human plays white, AI plays black
- **Visual**: Split board showing player vs AI distinction

#### Player vs Player Mode
- **White Side (rows 0-1)**: Warm colors
  - Warm white: (200, 200, 150)
  - Gold: (180, 150, 50)
- **Black Side (rows 6-7)**: Cool colors
  - Cool white: (150, 150, 200)
  - Blue: (50, 100, 180)
- **Purpose**: Two human players
- **Visual**: Warm vs cool colors distinguish sides

### 2. Piece Placement Feedback

#### Waiting for Pieces
Shows where pieces should be placed in starting position:
- **Empty squares (need pieces)**: Dim colored indicators
  - White side: (30, 30, 20) - Dim warm
  - Black side: (20, 20, 30) - Dim cool
- **Correctly placed**: Green (0, 100, 0)
- **Other squares**: Off (0, 0, 0)

**Use case**: Guides user through setting up board before game starts

#### Immediate Placement Feedback
Flash feedback when piece is placed:
- **Correct placement**: Bright green (0, 200, 0)
- **Incorrect placement**: Red (200, 0, 0)

**Use case**: Instant visual confirmation during setup

## Implementation

### LED Controller Methods

```python
def show_mode_selection(mode: str) -> None:
    """Display mode selection screen.
    
    Args:
        mode: "ai_vs_ai", "player_vs_ai", or "player_vs_player"
    """

def show_waiting_for_pieces(
    placed_squares: list[Square],
    correct_squares: list[Square]
) -> None:
    """Show board waiting for pieces to be placed.
    
    Args:
        placed_squares: Squares where pieces detected
        correct_squares: Squares where pieces should be
    """

def show_piece_placed_feedback(
    square: Square,
    is_correct: bool
) -> None:
    """Show immediate feedback when piece placed.
    
    Args:
        square: Square where piece was placed
        is_correct: Whether placement is correct
    """
```

## Tests Added

### Unit Tests (5)
- `test_mode_selection_ai_vs_ai` - Verify AI vs AI pattern
- `test_mode_selection_player_vs_ai` - Verify Player vs AI pattern
- `test_mode_selection_player_vs_player` - Verify Player vs Player pattern
- `test_waiting_for_pieces` - Verify piece placement indicators
- `test_piece_placed_feedback` - Verify correct/incorrect feedback

### Visualization Tests (8)
- `test_visualize_mode_selection_ai_vs_ai` - AI vs AI screen
- `test_visualize_mode_selection_player_vs_ai` - Player vs AI screen
- `test_visualize_mode_selection_player_vs_player` - Player vs Player screen
- `test_visualize_waiting_for_pieces_empty` - Empty board setup
- `test_visualize_waiting_for_pieces_partial` - Partially setup board
- `test_visualize_waiting_for_pieces_complete` - All pieces placed
- `test_visualize_piece_placed_correct` - Correct placement flash
- `test_visualize_piece_placed_incorrect` - Incorrect placement flash

## Generated Visualizations

All visualizations saved in `tests/output/leds/`:

### Mode Selection
- `led_mode_ai_vs_ai.png` - Cyan/purple alternating pattern
- `led_mode_player_vs_ai.png` - Split board (warm/AI colors)
- `led_mode_player_vs_player.png` - Split board (warm/cool colors)

### Piece Placement
- `led_waiting_empty.png` - All pieces needed (dim indicators)
- `led_waiting_partial.png` - Some pieces placed (green + dim)
- `led_waiting_complete.png` - All pieces placed (all green)
- `led_piece_placed_correct.png` - Bright green flash
- `led_piece_placed_incorrect.png` - Red flash

## Usage Flow

1. **Power on**: System initializes
2. **Mode selection**: Show mode options with distinct patterns
   - User selects mode (button/gesture/timeout)
3. **Piece placement**: Show where to place pieces
   - Dim indicators show empty positions
   - Green confirms correct placement
   - Red warns of incorrect placement
4. **Ready**: All pieces placed correctly
   - Board shows "ready" state
   - Game can begin

## Test Results

- **Total tests**: 98 (13 new)
- **Status**: ✅ All passing
- **Code quality**: ✅ Ruff + Mypy pass
- **Visualizations**: ✅ 8 new images generated

## Design Rationale

### Color Choices
- **AI colors**: Cyan/purple - tech/futuristic feeling
- **Player warm**: White/gold - human/inviting
- **Player cool**: White/blue - distinct from warm side
- **Feedback**: Green=good, Red=bad (universal convention)

### Patterns
- **Alternating squares**: Creates visual texture, easier to see
- **Dim indicators**: Not distracting but visible enough to guide
- **Flash feedback**: Immediate confirmation without sustained distraction

### Progressive Setup
- Start simple: Mode selection (3 clear choices)
- Guide user: Dim indicators show what's needed
- Confirm progress: Green shows what's done
- Clear feedback: Instant response to each action
