# 2D Platformer Game

A dynamic 2D platformer game built with Pygame featuring enemies, loot chests, and procedurally generated textures using AI.

## Features

- Player character with movement, jumping, and attack mechanics
- Enemies that patrol platforms and attack the player
- Loot chests with random rewards
- Camera system that follows the player
- Multiple game states (menu, playing, game over)
- **AI-Generated Textures**: Each time the game runs, it generates unique textures for backgrounds, platforms, enemies, and bosses
- Three progressively challenging levels with a final boss

## Requirements

- Python 3.x
- Pygame
- OpenAI API key (for texture generation)
- Pixel Lab access (for texture image generation)

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your API keys as environment variables:
   ```
   export OPENAI_API_KEY="your_openai_api_key_here"
   export PIXEL_LAB_API_KEY="your_pixel_lab_api_key_here"
   ```

3. Run the game:
   ```
   python main.py
   ```

## Controls

- Left/Right Arrow Keys: Move
- Space: Jump
- X: Attack
- Down Arrow: Open chests when near them

## AI Texture Generation Pipeline

This game features a unique texture generation pipeline that creates new game assets each time you play:

### How It Works

1. **Theme Selection**: The game randomly selects a theme for the level (e.g., medieval fantasy, sci-fi futuristic, post-apocalyptic wasteland).

2. **ChatGPT Integration**: Using the OpenAI API, the game generates detailed descriptions for:
   - Background textures for each level
   - Platform textures for each level
   - Enemy textures for each level
   - A boss texture for the final level

3. **Pixel Lab Integration**: The descriptions are sent to Pixel Lab, which generates pixel art textures based on these descriptions.

4. **In-Game Application**: The generated textures are applied to game elements, creating a unique visual experience each time you play.

### Technical Implementation

- `texture_generator.py`: Handles communication with the OpenAI API to generate texture descriptions
- `pixel_lab_integration.py`: Manages the integration with Pixel Lab to convert descriptions into actual texture images
- `level.py`: Uses the generated textures to create visually unique levels

### Fallback Mechanism

If API keys are not provided, the game will use placeholder textures while still maintaining gameplay functionality.
