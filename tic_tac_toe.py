import os
import random
import re

from dotenv import load_dotenv
from groq import Groq


# ==========================================
# TIC-TAC-TOE: HUMAN VS COMPUTER
# Random Strategy + Groq LLM Strategy
# ==========================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

# The model name is taken from the setup guide
# provided for this assignment.
MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq(api_key=API_KEY) if API_KEY else None

# Empty cells contain a space.
board = [" "] * 9

HUMAN = "X"
COMPUTER = "O"

# All possible winning combinations.
WINNING_COMBINATIONS = [
    (0, 1, 2),  # Row 1
    (3, 4, 5),  # Row 2
    (6, 7, 8),  # Row 3
    (0, 3, 6),  # Column 1
    (1, 4, 7),  # Column 2
    (2, 5, 8),  # Column 3
    (0, 4, 8),  # Main diagonal
    (2, 4, 6)   # Other diagonal
]


# ------------------------------------------
# Display the board
# ------------------------------------------

def display_board():
    print()

    for row in range(3):
        start = row * 3

        cells = []
        for col in range(3):
            index = start + col

            if board[index] == " ":
                cells.append(str(index + 1))
            else:
                cells.append(board[index])

        print(" " + " | ".join(cells))

        if row < 2:
            print("---+---+---")

    print()


# ------------------------------------------
# Check whether a player has won
# ------------------------------------------

def check_win(symbol):
    for a, b, c in WINNING_COMBINATIONS:
        if (
            board[a] == symbol
            and board[b] == symbol
            and board[c] == symbol
        ):
            return True

    return False


# ------------------------------------------
# Check whether the board is full
# ------------------------------------------

def board_full():
    return " " not in board


# ------------------------------------------
# Get all available cells
# ------------------------------------------

def available_cells():
    return [
        i for i in range(9)
        if board[i] == " "
    ]


# ------------------------------------------
# Human player's move
# ------------------------------------------

def get_human_move():
    while True:
        choice = input(
            "Choose an empty cell (1-9): "
        ).strip()

        # Reject non-numeric input.
        if not choice.isdigit():
            print("Invalid input! Enter a number from 1 to 9.")
            continue

        position = int(choice)

        # Reject numbers outside the board.
        if position < 1 or position > 9:
            print("Invalid choice! Enter a number from 1 to 9.")
            continue

        # Convert cell number to list index.
        index = position - 1

        # Reject an occupied cell.
        if board[index] != " ":
            print("That cell is already occupied. Try again.")
            continue

        return index


# ------------------------------------------
# Random computer strategy
# ------------------------------------------

def random_computer_move():
    moves = available_cells()

    if moves:
        return random.choice(moves)

    return None


# ------------------------------------------
# Find a move that completes a winning line
# ------------------------------------------

def find_winning_move(symbol):
    for position in available_cells():
        board[position] = symbol

        won = check_win(symbol)

        # Undo the temporary move.
        board[position] = " "

        if won:
            return position

    return None


# ------------------------------------------
# Local intelligent strategy
# Used as a fallback if the API fails.
# ------------------------------------------

def local_intelligent_move():
    # Priority 1: Win if possible.
    move = find_winning_move(COMPUTER)

    if move is not None:
        return move

    # Priority 2: Block the human's winning move.
    move = find_winning_move(HUMAN)

    if move is not None:
        return move

    # Priority 3: Take the center.
    if board[4] == " ":
        return 4

    # Priority 4: Choose an available corner.
    corners = [
        i for i in [0, 2, 6, 8]
        if board[i] == " "
    ]

    if corners:
        return random.choice(corners)

    # Priority 5: Choose an available side.
    sides = [
        i for i in [1, 3, 5, 7]
        if board[i] == " "
    ]

    if sides:
        return random.choice(sides)

    return None


# ------------------------------------------
# Groq LLM intelligent strategy
# ------------------------------------------

def llm_computer_move():
    if client is None:
        print("\nAPI key not found.")
        print("Using the local intelligent strategy instead.")
        return local_intelligent_move()

    # Show empty cells as numbers so the model
    # can identify the legal moves.
    board_text = ""

    for row in range(3):
        cells = []

        for col in range(3):
            index = row * 3 + col

            if board[index] == " ":
                cells.append(str(index + 1))
            else:
                cells.append(board[index])

        board_text += " | ".join(cells)

        if row < 2:
            board_text += "\n---------\n"

    legal_moves = [
        str(i + 1) for i in available_cells()
    ]

    prompt = f"""
You are choosing a move in a Tic-Tac-Toe game.

You are O. The human player is X.

Current board:
{board_text}

Legal empty cells: {", ".join(legal_moves)}

Choose exactly ONE cell number from the legal empty cells.

Priority:
1. Win immediately if possible.
2. Otherwise, block X from winning immediately.
3. Otherwise, prefer the center.
4. Otherwise, prefer a corner.
5. Otherwise, choose a side.

Return ONLY the single digit representing your move.
Do not include explanations, punctuation, or other text.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Tic-Tac-Toe move selector. "
                        "Return only one legal cell number."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        answer = response.choices[0].message.content.strip()

        # Accept only a single digit from 1 to 9.
        if re.fullmatch(r"[1-9]", answer):
            position = int(answer) - 1

            # Verify that the suggested cell is empty.
            if board[position] == " ":
                print("Move selected using the Groq LLM API.")
                return position

        print("The API returned an invalid move.")
        print("Using the local intelligent strategy.")

    except Exception as error:
        print("\nCould not get a valid API response.")
        print("Reason:", error)
        print("Using the local intelligent strategy instead.")

    return local_intelligent_move()


# ------------------------------------------
# Main game
# ------------------------------------------

def play_game():
    print("=" * 38)
    print("       TIC-TAC-TOE")
    print("=" * 38)

    print("\nChoose the computer strategy:")
    print("1. Random Move Strategy")
    print("2. Intelligent Move Strategy (Groq LLM)")

    while True:
        mode = input("Enter your choice (1 or 2): ").strip()

        if mode in ("1", "2"):
            break

        print("Invalid choice. Enter 1 or 2.")

    if mode == "1":
        print("\nRandom strategy selected.")

    else:
        print("\nIntelligent strategy selected.")

        if client is None:
            print("No API key detected.")
            print("The local intelligent strategy will be used.")
        else:
            print("Groq API key detected.")
            print("The program will attempt to use the LLM.")

    print("\nYou are X. The computer is O.")
    print("Choose cells using the numbers 1-9.")

    display_board()

    # The human always starts.
    while True:

        # Human turn
        print("Your turn (X).")
        human_move = get_human_move()

        board[human_move] = HUMAN

        display_board()

        if check_win(HUMAN):
            print("Congratulations! You win!")
            break

        if board_full():
            print("It's a draw!")
            break

        # Computer turn
        print("Computer's turn (O)...")

        if mode == "1":
            computer_move = random_computer_move()
            print("Computer used the random strategy.")
        else:
            computer_move = llm_computer_move()

        if computer_move is None:
            print("No moves remain. It's a draw!")
            break

        board[computer_move] = COMPUTER

        print(
            "Computer selected cell:",
            computer_move + 1
        )

        display_board()

        if check_win(COMPUTER):
            print("Computer wins! Better luck next time.")
            break

        if board_full():
            print("It's a draw!")
            break

    print("\nThanks for playing!")


# Run the game.
if __name__ == "__main__":
    play_game()