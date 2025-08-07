#!/usr/bin/env python3

"""
Prompt Customization Tool for AI Game Texture Generation

This tool allows you to:
- View and change themes
- Preview generated prompts
- Customize individual prompts
- Test texture generation with custom prompts
- Add new themes
"""

import sys
from prompt_manager import PromptManager
from pixel_lab_integration import PixelLabIntegration

class PromptCustomizer:
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.pixel_lab = PixelLabIntegration()
        
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("🎨 AI Game Texture Prompt Customization Tool")
        print("="*60)
        print("1. View current theme and prompts")
        print("2. Change theme")
        print("3. Preview all prompts")
        print("4. Customize a specific prompt")
        print("5. Add new theme")
        print("6. Generate textures with current settings")
        print("7. Test single texture generation")
        print("8. Reset to default prompts")
        print("0. Exit")
        print("-"*60)
        
    def view_current_settings(self):
        """Show current theme and sample prompts"""
        current_theme = self.prompt_manager.get_current_theme()
        print(f"\n📋 Current Settings:")
        print(f"Theme: {current_theme['name']}")
        print(f"Description: {current_theme['description']}")
        
        print(f"\n🎯 Sample Prompts:")
        for level in [1, 2, 3]:
            print(f"\nLevel {level}:")
            for texture_type in ["background", "platform", "enemy"]:
                if level == 3 and texture_type == "enemy":
                    continue  # Skip enemy for level 3, show boss instead
                prompt = self.prompt_manager.generate_prompt(texture_type, level)
                print(f"  {texture_type.capitalize()}: {prompt[:80]}...")
            
            if level == 3:
                prompt = self.prompt_manager.generate_prompt("boss", level)
                print(f"  Boss: {prompt[:80]}...")
    
    def change_theme(self):
        """Allow user to change the current theme"""
        themes = self.prompt_manager.get_available_themes()
        current = self.prompt_manager.config["current_theme"]
        
        print(f"\n🎨 Available Themes:")
        for i, (key, name) in enumerate(themes.items(), 1):
            marker = " (current)" if key == current else ""
            print(f"{i}. {name}{marker}")
        
        try:
            choice = input(f"\nSelect theme (1-{len(themes)}) or 'c' to cancel: ").strip()
            if choice.lower() == 'c':
                return
                
            choice_num = int(choice)
            if 1 <= choice_num <= len(themes):
                theme_key = list(themes.keys())[choice_num - 1]
                if self.prompt_manager.set_theme(theme_key):
                    print(f"✅ Theme changed to: {themes[theme_key]}")
                    self.view_current_settings()
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Invalid input")
    
    def preview_all_prompts(self):
        """Show all generated prompts"""
        self.prompt_manager.preview_prompts()
    
    def customize_prompt(self):
        """Allow user to customize a specific prompt"""
        print(f"\n✏️  Customize Specific Prompt")
        
        # Select level
        try:
            level = int(input("Enter level (1-3): "))
            if level not in [1, 2, 3]:
                print("❌ Invalid level")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Select texture type
        texture_types = ["background", "platform", "enemy"]
        if level == 3:
            texture_types.append("boss")
        
        print(f"\nTexture types for level {level}:")
        for i, texture_type in enumerate(texture_types, 1):
            print(f"{i}. {texture_type.capitalize()}")
        
        try:
            choice = int(input(f"Select texture type (1-{len(texture_types)}): "))
            if 1 <= choice <= len(texture_types):
                texture_type = texture_types[choice - 1]
            else:
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Show current prompt
        current_prompt = self.prompt_manager.generate_prompt(texture_type, level)
        print(f"\n📝 Current prompt for Level {level} {texture_type.capitalize()}:")
        print(f"'{current_prompt}'")
        
        # Get new prompt
        print(f"\n💡 Tips:")
        print(f"- Use {{theme_description}} to insert current theme")
        print(f"- Keep 'pixel art' style for consistency")
        print(f"- Be specific about details you want")
        
        new_prompt = input(f"\nEnter new prompt template (or 'c' to cancel): ").strip()
        if new_prompt.lower() == 'c':
            return
        
        if new_prompt:
            if self.prompt_manager.update_prompt(level, texture_type, new_prompt):
                print(f"✅ Prompt updated successfully!")
                
                # Show the new generated prompt
                updated_prompt = self.prompt_manager.generate_prompt(texture_type, level)
                print(f"\n🆕 New generated prompt:")
                print(f"'{updated_prompt}'")
            else:
                print("❌ Failed to update prompt")
    
    def add_new_theme(self):
        """Allow user to add a new theme"""
        print(f"\n➕ Add New Theme")
        
        theme_key = input("Enter theme key (lowercase, no spaces): ").strip().lower()
        if not theme_key or ' ' in theme_key:
            print("❌ Invalid theme key")
            return
        
        theme_name = input("Enter theme display name: ").strip()
        if not theme_name:
            print("❌ Theme name required")
            return
        
        theme_description = input("Enter theme description: ").strip()
        if not theme_description:
            print("❌ Theme description required")
            return
        
        if self.prompt_manager.add_theme(theme_key, theme_name, theme_description):
            print(f"✅ Added new theme: {theme_name}")
            
            # Ask if they want to switch to it
            switch = input("Switch to this theme now? (y/n): ").strip().lower()
            if switch == 'y':
                self.prompt_manager.set_theme(theme_key)
        else:
            print("❌ Failed to add theme")
    
    def generate_all_textures(self):
        """Generate all textures with current settings"""
        print(f"\n🎨 Generating All Textures...")
        
        try:
            texture_files = self.pixel_lab.generate_textures_with_custom_prompts()
            
            print(f"\n✅ Texture generation complete!")
            print(f"📁 Check these folders:")
            print(f"  - Game textures: assets/textures/")
            print(f"  - Verification copies: assets/pixellab_generated/")
            
            # Show generated files
            for level_num, textures in texture_files.items():
                print(f"\nLevel {level_num}:")
                for texture_type, filename in textures.items():
                    print(f"  ✓ {texture_type.capitalize()}")
                    
        except Exception as e:
            print(f"❌ Error generating textures: {e}")
    
    def test_single_texture(self):
        """Test generation of a single texture"""
        print(f"\n🧪 Test Single Texture Generation")
        
        # Select level and texture type (similar to customize_prompt)
        try:
            level = int(input("Enter level (1-3): "))
            if level not in [1, 2, 3]:
                print("❌ Invalid level")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        texture_types = ["background", "platform", "enemy"]
        if level == 3:
            texture_types.append("boss")
        
        print(f"\nTexture types:")
        for i, texture_type in enumerate(texture_types, 1):
            print(f"{i}. {texture_type.capitalize()}")
        
        try:
            choice = int(input(f"Select texture type (1-{len(texture_types)}): "))
            if 1 <= choice <= len(texture_types):
                texture_type = texture_types[choice - 1]
            else:
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Generate the texture
        prompt = self.prompt_manager.generate_prompt(texture_type, level)
        print(f"\n📝 Using prompt: '{prompt}'")
        print(f"🎨 Generating texture...")
        
        try:
            _, filename = self.pixel_lab.generate_texture_image(prompt, texture_type, level)
            print(f"✅ Generated: {filename}")
            
            # Also show verification copy location
            pixellab_filename = self.pixel_lab._get_pixellab_filename(texture_type, level)
            print(f"📋 Verification copy: {pixellab_filename}")
            
        except Exception as e:
            print(f"❌ Error generating texture: {e}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        confirm = input("⚠️  Reset all prompts to defaults? This cannot be undone. (y/N): ").strip().lower()
        if confirm == 'y':
            # Reload default config
            self.prompt_manager.config = self.prompt_manager.get_default_config()
            if self.prompt_manager.save_config():
                print("✅ Reset to default prompts")
            else:
                print("❌ Failed to reset")
    
    def run(self):
        """Main program loop"""
        while True:
            self.show_menu()
            
            try:
                choice = input("Select option (0-8): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                elif choice == '1':
                    self.view_current_settings()
                elif choice == '2':
                    self.change_theme()
                elif choice == '3':
                    self.preview_all_prompts()
                elif choice == '4':
                    self.customize_prompt()
                elif choice == '5':
                    self.add_new_theme()
                elif choice == '6':
                    self.generate_all_textures()
                elif choice == '7':
                    self.test_single_texture()
                elif choice == '8':
                    self.reset_to_defaults()
                else:
                    print("❌ Invalid option")
                    
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    customizer = PromptCustomizer()
    customizer.run()
