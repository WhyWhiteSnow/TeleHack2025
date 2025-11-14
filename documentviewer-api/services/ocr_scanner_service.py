import pdfplumber
import io
import re
from typing import Dict, List, Any, Optional


class OCRScannerService:
    def process_pdf(self, pdf_bytes: bytes) -> dict:
        result = {"status": "success", "data": {}, "tables": []}
        special_word = "<UNKNOWN>"

        try:
            pdf_file = io.BytesIO(pdf_bytes)

            full_text = ""
            all_tables = []

            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n--- Страница {page_num + 1} ---\n{page_text}"
                    page_tables = page.extract_tables()

                    for table_num, table in enumerate(page_tables):
                        if table and any(
                            any(cell is not None for cell in row) for row in table
                        ):
                            cleaned_table = self.clean_table(table)
                            if cleaned_table:
                                table_info = {
                                    "page": page_num + 1,
                                    "table_number": table_num + 1,
                                    "data": cleaned_table,
                                    "type": self.detect_table_type(cleaned_table),
                                }
                                all_tables.append(table_info)

            if not full_text and not all_tables:
                result["status"] = "error"
                result["message"] = "Не удалось извлечь данные из PDF"
                return result

            extracted_data = self.parse_text_fields(full_text)

            table_data = self.process_tables(all_tables, full_text)

            merged_data = self.merge_data(extracted_data, table_data)

            result["data"] = self.build_structured_result(merged_data, special_word)
            result["tables"] = all_tables

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Ошибка обработки PDF: {str(e)}"

        return result

    def clean_table(self, table: List[List[Optional[str]]]) -> List[List[str]]:
        cleaned = []
        for row in table:
            cleaned_row = []
            has_data = False
            for cell in row:
                if cell is not None and str(cell).strip():
                    cleaned_cell = str(cell).strip()
                    cleaned_row.append(cleaned_cell)
                    has_data = True
                else:
                    cleaned_row.append("")
            if has_data:
                cleaned.append(cleaned_row)
        return cleaned

    def detect_table_type(self, table_data: List[List[str]]) -> str:
        if not table_data:
            return "unknown"

        headers = " ".join(table_data[0]).lower()

        product_keywords = ["товар", "услуга", "наименование", "описание", "артикул"]
        price_keywords = ["цена", "стоимость", "сумма", "итого", "всего"]
        quantity_keywords = ["количество", "кол-во", "шт", "кг"]

        has_products = any(keyword in headers for keyword in product_keywords)
        has_prices = any(keyword in headers for keyword in price_keywords)
        has_quantity = any(keyword in headers for keyword in quantity_keywords)

        if has_products and (has_prices or has_quantity):
            return "products"
        elif any(word in headers for word in ["реквизит", "банк", "счет", "бик"]):
            return "bank_details"
        elif any(word in headers for word in ["итого", "всего", "сумма"]):
            return "totals"
        else:
            return "general"

    def parse_text_fields(self, text: str) -> Dict[str, Any]:
        patterns = {
            "supplier_inn": r"ИНН\s*(\d{10,12})",
            "supplier_name": r"Поставщик[:\s]+([^\n]+)",
            "buyer_name": r"(?:Плательщик|Покупатель|Заказчик)[:\s]+([^\n]+)",
            "amount": r"(?:Сумма|Итого)\s*[:\s]*([\d\s,]+(?:\s*руб)?)",
            "invoice_number": r"(?:Счет|Счёт)[\s№]*([^\n]+)",
            "date": r"(\d{2}\.\d{2}\.\d{4})",
            "bank_account": r"(?:р\/с|расч[ёе]тный сч[ёе]т)\s*([^\n]+)",
            "bik": r"БИК\s*(\d{9})",
            "contract_number": r"(?:Договор|Дог\.)\s*[№\s]*([^\n]+)",
        }

        extracted_data = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            extracted_data[field] = match.group(1).strip() if match else None

        return extracted_data

    def process_tables(self, tables: List[Dict], full_text: str) -> Dict[str, Any]:
        table_data = {"products": [], "bank_details": {}, "totals": {}}

        for table_info in tables:
            table_type = table_info["type"]
            table = table_info["data"]

            if not table:
                continue

            if table_type == "products":
                products = self.extract_products_from_table(table)
                table_data["products"].extend(products)

            elif table_type == "bank_details":
                bank_info = self.extract_bank_details_from_table(table)
                table_data["bank_details"].update(bank_info)

            elif table_type == "totals":
                totals = self.extract_totals_from_table(table)
                table_data["totals"].update(totals)

        return table_data

    def extract_products_from_table(
        self, table: List[List[str]]
    ) -> List[Dict[str, Any]]:
        products = []

        if len(table) < 2:
            return products

        headers = [h.lower() for h in table[0]]

        name_col = self.find_column_index(
            headers, ["наименование", "товар", "услуга", "описание"]
        )
        quantity_col = self.find_column_index(headers, ["количество", "кол-во", "шт"])
        price_col = self.find_column_index(headers, ["цена", "стоимость"])
        amount_col = self.find_column_index(headers, ["сумма", "amount", "итого"])

        for row in table[1:]:
            if not any(cell.strip() for cell in row if cell):
                continue

            product = {
                "name": row[name_col]
                if name_col is not None and name_col < len(row)
                else "",
                "quantity": row[quantity_col]
                if quantity_col is not None and quantity_col < len(row)
                else "",
                "price": row[price_col]
                if price_col is not None and price_col < len(row)
                else "",
                "amount": row[amount_col]
                if amount_col is not None and amount_col < len(row)
                else "",
            }

            product = {k: v for k, v in product.items() if v.strip()}

            if product:
                products.append(product)

        return products

    def extract_bank_details_from_table(self, table: List[List[str]]) -> Dict[str, str]:
        bank_details = {}
        for row in table:
            if len(row) >= 2:
                key = row[0].lower().strip() if row[0] else ""
                value = row[1].strip() if len(row) > 1 and row[1] else ""

                if key and value:
                    if "банк" in key:
                        bank_details["bank_name"] = value
                    elif "счет" in key or "р/с" in key:
                        bank_details["account_number"] = value
                    elif "бик" in key:
                        bank_details["bik"] = value
                    elif "корр" in key:
                        bank_details["correspondent_account"] = value
                    elif "инн" in key:
                        bank_details["inn"] = value

        return bank_details

    def extract_totals_from_table(self, table: List[List[str]]) -> Dict[str, str]:
        totals = {}

        for row in table:
            row_text = " ".join(str(cell) for cell in row if cell).lower()
            if any(word in row_text for word in ["итого", "всего", "сумма", "total"]):
                for cell in reversed(row):
                    if cell and any(char.isdigit() for char in str(cell)):
                        totals["total_amount"] = str(cell).strip()
                        break

        return totals

    def find_column_index(
        self, headers: List[str], keywords: List[str]
    ) -> Optional[int]:
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in keywords):
                return i
        return None

    def merge_data(
        self, text_data: Dict[str, Any], table_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = text_data.copy()

        if table_data.get("bank_details"):
            if "bank_details" not in merged:
                merged["bank_details"] = {}
            merged["bank_details"].update(table_data["bank_details"])

        if table_data.get("products"):
            merged["products"] = table_data["products"]

        if table_data.get("totals"):
            merged.update(table_data["totals"])

        return merged

    def build_structured_result(
        self, data: Dict[str, Any], special_word: str
    ) -> Dict[str, Any]:
        # Основная структура
        result = {
            "supplier": {
                "name": data.get("supplier_name", special_word),
                "inn": data.get("supplier_inn", special_word),
            },
            "buyer": {"name": data.get("buyer_name", special_word)},
            "payment_details": {
                "amount": data.get("amount", data.get("total_amount", special_word)),
                "bank_account": data.get(
                    "bank_account",
                    data.get("bank_details", {}).get("account_number", special_word),
                ),
                "bik": data.get(
                    "bik", data.get("bank_details", {}).get("bik", special_word)
                ),
            },
            "document_info": {
                "number": data.get("invoice_number", special_word),
                "date": data.get("date", special_word),
                "contract_number": data.get("contract_number", special_word),
            },
        }

        if "products" in data and data["products"]:
            result["products"] = data["products"]

        bank_details = data.get("bank_details", {})
        if bank_details:
            result["payment_details"]["bank_name"] = bank_details.get(
                "bank_name", special_word
            )
            result["payment_details"]["correspondent_account"] = bank_details.get(
                "correspondent_account", special_word
            )

        result = self.remove_unknown_values(result, special_word)

        return result

    def remove_unknown_values(self, data: Any, special_word: str) -> Any:
        if isinstance(data, dict):
            return {
                k: self.remove_unknown_values(v, special_word)
                for k, v in data.items()
                if v != special_word
                and self.remove_unknown_values(v, special_word) not in [None, "", {}]
            }
        elif isinstance(data, list):
            return [
                self.remove_unknown_values(item, special_word)
                for item in data
                if self.remove_unknown_values(item, special_word) not in [None, "", {}]
            ]
        else:
            return data


ocr_scanner_service = OCRScannerService()
