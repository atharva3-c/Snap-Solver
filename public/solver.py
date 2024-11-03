import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
import sys
import json  # Import the json module

# Set the path to your Tesseract-OCR installation
pytesseract.pytesseract.tesseract_cmd = 'C:/Users/Atharva Chepe/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

SUDOKU_GRID_WIDTH = 468
SUDOKU_GRID_HEIGHT = 450

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    return image, thresholded

def find_largest_contour(thresholded_image):
    contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    return largest_contour

def get_warped_image(image, largest_contour):
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)

    if len(approx) == 4:
        points = np.array([point[0] for point in approx], dtype='float32')
        s = points.sum(axis=1)
        diff = np.diff(points, axis=1)
        top_left = points[np.argmin(s)]
        bottom_right = points[np.argmax(s)]
        top_right = points[np.argmin(diff)]
        bottom_left = points[np.argmax(diff)]
        
        rect = np.array([top_left, top_right, bottom_right, bottom_left], dtype='float32')

        dst = np.array([[0, 0], [SUDOKU_GRID_WIDTH - 1, 0], [SUDOKU_GRID_WIDTH - 1, SUDOKU_GRID_HEIGHT - 1], [0, SUDOKU_GRID_HEIGHT - 1]], dtype='float32')

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (SUDOKU_GRID_WIDTH, SUDOKU_GRID_HEIGHT))
        return warped
    else:
        raise ValueError("The Sudoku grid was not found properly.")

def extract_cells(warped_image, cell_width, cell_height):
    cells = []
    for row in range(9):
        for col in range(9):
            x = col * cell_width
            y = row * cell_height
            cell = warped_image[y:y + cell_height, x:x + cell_width]
            cells.append(cell)
    return cells

def preprocess_cells(cells, margin=3):
    preprocessed_cells = []
    for cell in cells:
        gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        trimmed_cell = gray_cell[margin:-margin, margin:-margin]
        trimmed_cell = cv2.bitwise_not(trimmed_cell)  
        
        alpha = 2.0 
        beta = 0    
        adjusted = cv2.convertScaleAbs(trimmed_cell, alpha=alpha, beta=beta)
        _, cell_binary = cv2.threshold(adjusted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_cells.append(cell_binary)
    return preprocessed_cells

def resize_cells(preprocessed_cells):
    resized_cells = []
    for cell in preprocessed_cells:
        resized_cell = cell[3:-3, 3:-3]  # Crop 3 units from each edge
        resized_cells.append(resized_cell)
    return resized_cells

def recognize_digits(cells):
    recognized_digits = []
    custom_config = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
    for cell in cells:
        digit = pytesseract.image_to_string(cell, config=custom_config).strip()
        if digit.isdigit():
            recognized_digits.append(int(digit))
        else:
            recognized_digits.append(0)  # If no digit is recognized, append 0
    return recognized_digits

def build_sudoku_board(recognized_digits):
    board = []
    idx = 0
    for _ in range(9):
        row = []
        for _ in range(9):
            digit = recognized_digits[idx]
            if digit > 9:  # Just in case, take only the units digit
                digit = digit % 10
            row.append(digit)
            idx += 1
        board.append(row)
    return board

def solve(board):
    find = find_empty(board)
    if not find:
        return True
    else:
        row, col = find

    for i in range(1, 10):
        if valid(board, i, (row, col)):
            board[row][col] = i
            if solve(board):
                return True
            board[row][col] = 0
    return False

def valid(board, num, pos):
    for i in range(len(board[0])):
        if board[pos[0]][i] == num and pos[1] != i:
            return False
   
    for i in range(len(board)):
        if board[i][pos[1]] == num and pos[0] != i:
            return False

    box_x = pos[1] // 3
    box_y = pos[0] // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if board[i][j] == num and (i, j) != pos:
                return False
    return True

def print_board(board):
    for i in range(len(board)):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")
        for j in range(len(board[0])):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")
            if j == 8:
                print(board[i][j])
            else:
                print(str(board[i][j]) + " ", end="")

def find_empty(board):
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == 0:
                return (i, j)  # row, col
    return None

# Main code
if __name__ == "__main__":
    # Get the image path from the command line arguments
    image_path = sys.argv[1]

    image, thresholded_image = preprocess_image(image_path)

    largest_contour = find_largest_contour(thresholded_image)
    warped_image = get_warped_image(image, largest_contour)

    cell_width = SUDOKU_GRID_WIDTH // 9
    cell_height = SUDOKU_GRID_HEIGHT // 9

    cells = extract_cells(warped_image, cell_width, cell_height)
    preprocessed_cells = preprocess_cells(cells, margin=3)
    resized_cells = resize_cells(preprocessed_cells)
    recognized_digits = recognize_digits(resized_cells)

    sudoku_board = build_sudoku_board(recognized_digits)

    # Prepare the result to be returned as JSON
    if solve(sudoku_board):
        result = {
            "success": True,
            "solved_board": sudoku_board
        }
    else:
        result = {
            "success": False,
            "message": "No solution exists for the given Sudoku board."
        }

    # Print the result as a JSON string
    print(json.dumps(result))  # Output the result
