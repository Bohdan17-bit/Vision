import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from TextSpanPDF import TextSpanPDF


class ParserWeb:
    def __init__(self):
        self.list_spans = []

    def parse_webpage(self, url):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--start-maximized")  #
        service = Service('C:/chr-drv/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        # JavaScript для обгортання кожного слова в <span class="word">
        driver.execute_script("""
            const allElements = document.querySelectorAll('*:not(script):not(style)');
            allElements.forEach(elem => {
                if (elem.children.length === 0 && elem.textContent.trim() !== '') {
                    const parts = elem.textContent.split(/(\\s+|\\b)/);
                    elem.innerHTML = parts.map(part => {
                        if (part.trim() !== '') {
                            return `<span class="word">${part}</span>`;
                        } else {
                            return part;
                        }
                    }).join('');
                }
            });
        """)

        elements = driver.find_elements(By.CLASS_NAME, "word")

        for elem in elements:
            text = elem.text.strip()
            if text:
                style = self.get_style_properties(driver, elem)
                font_size = self.extract_font_size(style.get("fontSize", ""))
                #font_weight = self.extract_font_weight(style.get("fontWeight", ""))
                #font_style = style.get("fontStyle", "normal")
                color = style.get("color", "black")
                x1, y1, x2, y2 = self.get_element_coordinates(driver, elem)
                word_span = TextSpanPDF()
                text = text.lower()
                word_span.set_text(text)
                word_span.set_size_text(font_size)
                word_span.set_background_color("")
                word_span.set_color_text(color)
                word_span.set_coords(x1, y1, x2, y2)
                word_span.set_flags("")
                self.list_spans.append(word_span)

        driver.quit()
        return self.list_spans

    def get_style_properties(self, driver, element):
        script = """
        const elem = arguments[0];
        const style = window.getComputedStyle(elem);
        return {
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            fontStyle: style.fontStyle,
            color: style.color
        };
        """
        return driver.execute_script(script, element)

    def extract_font_size(self, font_size_str):
        match = re.match(r"(\d+(\.\d+)?)px", font_size_str)
        if match:
            return float(match.group(1))
        return None

    def extract_font_weight(self, font_weight_str):
        try:
            weight = int(font_weight_str)
            if weight == 400:
                return "normal"
            elif weight == 700:
                return "bold"
            else:
                return str(weight)
        except ValueError:
            return font_weight_str

    def get_element_coordinates(self, driver, element):
        script = """
        const rect = arguments[0].getBoundingClientRect();
        return [rect.left, rect.top, rect.right, rect.bottom];
        """
        return driver.execute_script(script, element)