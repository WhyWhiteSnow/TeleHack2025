import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import pdf2image
from typing import Dict, Any
import os
from loguru import logger

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    poppler_path = r"D:\poopler\poppler-25.11.0\Library\bin"
else:
    # Check possible installation paths
    possible_paths = ["/usr/bin/tesseract", "/usr/local/bin/tesseract", "/bin/tesseract"]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract found: {path}")
            break
    # If not found, use which command
    import subprocess

    result = subprocess.run(["which", "tesseract"], capture_output=True, text=True)
    if result.returncode == 0:
        pytesseract.pytesseract.tesseract_cmd = result.stdout.strip()
        logger.info(f"Tesseract found via which: {pytesseract.pytesseract.tesseract_cmd}")
    else:
        logger.critical(
            "WARNING: Tesseract not found in the system. Install it using your package manager."
        )
        raise Exception("Tesseract not found in the system. Install it using your package manager.")


def pdf_bytes_to_images(pdf_bytes: bytes) -> list:
    """
    Convert PDF from bytes to image list
    """
    try:
        # Use pdf2image to convert PDF to images
        if os.name == "nt":
            images = pdf2image.convert_from_bytes(pdf_bytes, dpi=300, poppler_path=poppler_path)
        else:
            images = pdf2image.convert_from_bytes(pdf_bytes, dpi=300)
        return images
    except Exception as e:
        logger.error(f"Error converting PDF: {e}")
        return []


def preprocess_image(image):
    """Image preprocessing for improving text recognition"""
    if isinstance(image, Image.Image):
        # Convert PIL Image to numpy array
        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if len(image.shape) == 3:
        height, width, channels = image.shape
    else:
        height, width = image.shape
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Upscale image
    image = cv2.resize(image, (width * 2, height * 2))

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.medianBlur(gray, 3)
    thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]

    # Remove small noise using morphological operations
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

    return cleaned


def recognize_text_in_roi(image, roi):
    """Recognize text in the region of interest (ROI)"""
    x, y, w, h = roi

    # Check coordinates
    if (
        x >= 0
        and y >= 0
        and w > 5
        and h > 5
        and x + w <= image.shape[1]
        and y + h <= image.shape[0]
    ):
        cell_image = image[y : y + h, x : x + w]

        # Cell preprocessing to improve recognition
        processed_cell = preprocess_image(cell_image)

        # Text recognition
        try:
            text = pytesseract.image_to_string(
                processed_cell,
                lang="rus",
            )

            # Text cleaning
            text = " ".join(text.split()).strip()
            return text if text else ""
        except Exception as e:
            logger.info(f"Error recognizing text: {e}")
            return ""

    return ""


def find_cells_in_table(table_region, offset_x=0, offset_y=0):
    """Find cells in the table"""
    if len(table_region.shape) == 3:
        table_region = cv2.cvtColor(table_region, cv2.COLOR_BGR2GRAY)

    # Better binarization with adaptive threshold
    thresh = cv2.adaptiveThreshold(
        table_region, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5
    )

    # Improve table lines
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))

    # Find horizontal and vertical lines
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_horizontal)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_vertical)

    # Combine vertical and horizontal lines
    grid_lines = cv2.add(horizontal_lines, vertical_lines)

    # Thicken lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    grid_lines = cv2.dilate(grid_lines, kernel, iterations=2)

    # Fill line gaps
    grid_lines = cv2.morphologyEx(grid_lines, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(grid_lines, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours
    cell_contours = []
    min_cell_area = 100  # Minimum cell size

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_cell_area:
            # Contour approximation
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            # Look for rectangular shapes
            if len(approx) >= 4:
                # Check aspect ratio
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.1 < aspect_ratio < 10.0:
                    # Shift contour back to original image
                    shifted_cnt = approx + np.array([offset_x, offset_y])
                    cell_contours.append(shifted_cnt)

    return cell_contours


def detect_table_cells_advanced(image):
    """Detect tables and cells with text recognition"""
    if isinstance(image, Image.Image):
        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binarization
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Create horizontal and vertical kernels
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))

    # Apply morphological operations
    horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_horizontal)
    vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_vertical)

    # Combine
    table_structure = cv2.add(horizontal, vertical)

    # Thicken lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    table_structure = cv2.dilate(table_structure, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by area and take the largest ones (presumably tables)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    result_dict = {}

    for table_idx, cnt in enumerate(contours, 1):
        # Approximate contour
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) >= 4:  # Allow non-rectangular shapes
            # Get table bounding rectangle
            x, y, w, h = cv2.boundingRect(approx)

            # Expand table area for cell detection
            expand = 5
            x_exp = max(0, x - expand)
            y_exp = max(0, y - expand)
            w_exp = min(image.shape[1] - x_exp, w + 2 * expand)
            h_exp = min(image.shape[0] - y_exp, h + 2 * expand)

            # Extract table region
            table_region = gray[y_exp : y_exp + h_exp, x_exp : x_exp + w_exp]

            # Find cells within the table
            cell_contours = find_cells_in_table(table_region, x_exp, y_exp)

            # Recognize text in each cell
            table_cells_dict = {}

            for cell_idx, cell in enumerate(cell_contours, 1):
                # Get cell coordinates
                x_cell, y_cell, w_cell, h_cell = cv2.boundingRect(cell)

                # Recognize text in the cell
                text = recognize_text_in_roi(image, (x_cell, y_cell, w_cell, h_cell))

                # Add to cells dictionary
                table_cells_dict[f"cell_{cell_idx}"] = text

            # Add table to result only if it has cells with text
            if table_cells_dict:
                result_dict[f"table_{table_idx}"] = table_cells_dict

    return result_dict


def detect_table_edges_with_ocr(image):
    """Alternative method for table detection with text recognition"""
    if isinstance(image, Image.Image):
        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Canny edge detector
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Morphological operations to connect line breaks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by area and approximate
    min_area = 1000  # Minimum contour area
    table_contours = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            # Approximate contour to rectangle
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) == 4:
                table_contours.append(approx)

    result_dict = {}

    # Find cells within tables and recognize text
    for table_idx, table_cnt in enumerate(table_contours, 1):
        # Get table bounding rectangle
        x, y, w, h = cv2.boundingRect(table_cnt)

        # Expand search area
        expand = 10
        x_exp = max(0, x - expand)
        y_exp = max(0, y - expand)
        w_exp = min(gray.shape[1] - x_exp, w + 2 * expand)
        h_exp = min(gray.shape[0] - y_exp, h + 2 * expand)

        # Extract expanded table region
        table_region = gray[y_exp : y_exp + h_exp, x_exp : x_exp + w_exp]

        # Find cells within the table
        cell_contours = find_cells_in_table(table_region, x_exp, y_exp)

        # Recognize text in each cell
        table_cells_dict = {}

        for cell_idx, cell in enumerate(cell_contours, 1):
            # Get cell coordinates
            x_cell, y_cell, w_cell, h_cell = cv2.boundingRect(cell)

            # Recognize text in the cell
            text = recognize_text_in_roi(image, (x_cell, y_cell, w_cell, h_cell))

            # Add to cells dictionary
            table_cells_dict[f"cell_{cell_idx}"] = text

        # Add table to result only if it has cells with text
        if table_cells_dict:
            result_dict[f"table_{table_idx}"] = table_cells_dict

    return result_dict


def process_pdf_document(pdf_bytes: bytes, method: str = "advanced") -> Dict[str, Any]:
    """
    Main function for processing PDF documents with tables

    Args:
        pdf_bytes: PDF document as bytes
        method: table detection method ('advanced' or 'edges')

    Returns:
        Dictionary with recognition results in format:
        {
            "page_1": {
                "table_1": {
                    "cell_1": "text",
                    "cell_2": "text",
                    ...
                },
                ...
            },
            ...
        }
    """
    # Convert PDF to images
    images = pdf_bytes_to_images(pdf_bytes)

    if not images:
        return {"error": "Failed to extract images from PDF"}

    results = {}

    # Process each page
    for page_num, image in enumerate(images, 1):
        try:
            if method == "advanced":
                page_result = detect_table_cells_advanced(image)
            else:
                page_result = detect_table_edges_with_ocr(image)

            if page_result:
                results[f"page_{page_num}"] = page_result
            else:
                results[f"page_{page_num}"] = {"info": "No tables detected"}

        except Exception as e:
            results[f"page_{page_num}"] = {"error": f"Processing error: {str(e)}"}

    return results


# Example usage in web application
def handle_pdf_upload(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Function for processing uploaded PDF in web application

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Dictionary with recognition results
    """
    try:
        # Process PDF
        result = process_pdf_document(pdf_bytes, method="advanced")
        return {
            "success": True,
            "data": result,
            "message": "Processing completed successfully",
        }
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"Error processing PDF: {str(e)}",
        }
