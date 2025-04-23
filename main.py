# main.py
# Entry point for the Python Civ Sim game.
import sys # Needed for sys.exit
import pygame # Needed for pygame.error and cleanup
import traceback # For detailed error reporting

# Import the main Game class AFTER checking dependencies/version if needed
from game import Game

# --- Optional Version Check ---
# if sys.version_info < (3, 9): # Example check
#     print("Python 3.9 or higher is recommended.")
#     # sys.exit(1) # Exit if version too low

if __name__ == '__main__':
    print("Starting Python Civ Sim Prototype...")
    game_instance = None # Initialize to None
    try:
        game_instance = Game() # Create an instance of the game
        game_instance.run()    # Start the main game loop

    # Catch specific Pygame errors first if possible
    except pygame.error as pg_err:
        print("\n--- A Pygame Error Occurred ---")
        print(pg_err)
        traceback.print_exc()
        print("---------------------------------")

    # Catch other potential exceptions during runtime
    except Exception as e: # Catch broader exceptions for unexpected issues
        print("\n--- An Unexpected Runtime Error Occurred ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
        traceback.print_exc()
        print("------------------------------------------")

    finally:
        # Ensure Pygame quits properly even if an error occurred
        # (quit_game handles this now, but this is extra safety)
        print("Ensuring Pygame quits...")
        pygame.quit()
        # No sys.exit here, let the script end naturally or via quit_game