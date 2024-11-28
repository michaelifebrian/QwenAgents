from PIL import Image
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import io
import time
from markdownify import markdownify as md
from selenium.webdriver.common.keys import Keys
from duckduckgo_search import DDGS
import re
import requests
from pathlib import Path
import json
import traceback
from apitoken import HF_TOKEN

imgCounter = 0
pythonOutputCounter = 0


def flux_generate_image(prompt: str):
    """
    create image using Flux.1 from prompt and display it. Use long specific prompt to make the image accurate.

    Args:
        prompt: The prompt to generate image from
    Returns:
        A confirmation of image displayed or not
    """
    print(f"Flux called with prompt: {prompt}")
    global imgCounter

    def quer(payload, api_url):
        responsesd = requests.post(api_url, headers=headers, json=payload)
        return responsesd.content

    try:
        API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
        headers = {"Authorization": f"Bearer {HF_TOKEN}", "x-use-cache": "false"}
        image_bytes = quer(
            {"inputs": prompt,
             "parameters": {
                 "guidance_scale": 3.5,
                 "num_inference_steps": 50,
                 "max_sequence_length": 512
             }, },
            API_URL
        )
        image = Image.open(io.BytesIO(image_bytes))
        imgCounter += 1
        image.save(f"image{imgCounter}.jpg")
        return {
            "status": f"Image generated and saved as image{imgCounter}.jpg"
        }
    except Exception as error:
        return {"status": f"Error: {error}"}


def search_engine_duckduckgo(keyword: str, max_results: int = 8):
    """
    search the web from a keyword. ALWAYS crosschecks the information by accessing the url, the information given from search engine is not updated.

    Args:
        keyword: The keyword to search for.
        max_results: The maximum number of results to return. Increase the number for more information.
    Returns:
        A dict list of search results.
    """
    try:
        results = DDGS().text(keyword, max_results=max_results)
        return results
    except Exception as error:
        return {"status": f"Error: {error}"}


def search_engine_google(keyword: str):
    """
    search the web from a keyword. ALWAYS crosschecks the information by accessing the url, the information given from search engine is not updated.

    Args:
        keyword: The keyword to search for.
    Returns:
        A dict list of search results.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument('--start-maximized')
    options.add_argument('window-size=1920x1080')
    # start session
    driver = webdriver.Chrome(options=options)
    returnResult = []
    try:
        # Navigate to Google
        driver.get("https://www.google.co.id")

        # # Find the search bar and input query
        search_box = driver.find_element(By.NAME, "q")
        search_query = keyword
        search_box.send_keys(search_query + Keys.RETURN)

        # Wait for results to load
        time.sleep(3)
        # html = driver.page_source
        # Extract search result elements
        results = driver.find_elements(By.CSS_SELECTOR, "div.g")
        # Loop through and extract title, link, and description
        for result in results:
            try:
                description = result.text
            except Exception:
                description = "No description"
            try:
                title_element = result.find_element(By.TAG_NAME, "h3")
                title = title_element.text
            except Exception:
                title = "No title"
            try:
                link_element = result.find_element(By.CSS_SELECTOR, "a")
                link = link_element.get_attribute("href")
            except Exception:
                link = "No link"
            result_data = {
                "title": title,
                "href": link,
                "body": description
            }
            returnResult.append(result_data)
    finally:
        # Close the driver
        driver.quit()
    return returnResult


def searchengine(keyword: str):
    """
    search the web from a keyword. Always crosschecks the information by accessing the url href, the information given from search engine is not updated.

    Args:
        keyword: The keyword to search for.
    Returns:
        A dict list of search results.
    """
    print(f"Search engine called with keyword: {keyword}")
    listResult = []
    listResult.extend(search_engine_duckduckgo(keyword))
    listResult.extend(search_engine_google(keyword))
    return listResult


def browser(url: str):
    """
    open and scrape the web from an url.

    Args:
        url: The url to open.
    Returns:
        The text of the web page.
    """
    print(f"Scrape web called with url: {url}")
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument('--start-maximized')
        options.add_argument('window-size=1920x1080')
        # start session
        browserdriver = webdriver.Chrome(options=options)
        browserdriver.get(url)
        time.sleep(7)
        html = browserdriver.page_source
        browserdriver.quit()
        txt = md(html)
        txt = re.sub('\n+', '\n', txt)
        txt = re.sub('\n +', '\n', txt)
        txt = re.sub('\n+', '\n', txt)
        txt = re.sub('\n +', '\n', txt)
        return {'url': url, 'content': txt}
    except Exception as error:
        return {"status": f"Error: {error}"}


def python_interpreter(code_string: str):
    """
    run Python code in jupyter environment and return its output and the snapshot of the cells output. Always use this to validate a generated python code.

    Args:
        code_string: The Python code to run.
    Returns:
        The output of the Python script.
    """
    print("Python interpreter called")
    global pythonOutputCounter
    pythonOutputCounter += 1

    code_string = json.loads(json.dumps(code_string))
    code_string = code_string.encode('utf-8').decode('unicode-escape')
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell(code_string))
    ep = ExecutePreprocessor(timeout=60, kernel_name='python3')
    try:
        nb_out, _ = ep.preprocess(nb)
        text_outputs = []
        for cell in nb_out.cells:
            if cell.cell_type == 'code':  # Only process code cells
                for output in cell.get('outputs', []):
                    if output.output_type == 'stream':
                        # Stream output (e.g., print statements)
                        text_outputs.append(output.get('text', ''))
                    elif output.output_type == 'execute_result':
                        # Execution result (e.g., Jupyter cell output)
                        data = output.get('data', {})
                        if 'text/plain' in data:
                            text_outputs.append(data['text/plain'])
                    elif output.output_type == 'error':
                        # Error output
                        text_outputs.append('\n'.join(output.get('traceback', [])))
        html_exporter = HTMLExporter()
        html_data, _ = html_exporter.from_notebook_node(nb_out)
        soup = BeautifulSoup(html_data, "html.parser")
        html_data = soup
        soup.find('div', class_='jp-Cell-inputWrapper').decompose()
        with open("output.html", "w") as html_file:
            html_file.write(str(html_data))
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=options)
        driver.get((Path.cwd() / "output.html").as_uri())
        height = driver.execute_script('return document.documentElement.scrollHeight')
        width = driver.execute_script('return document.documentElement.scrollWidth')
        driver.set_window_size(width, height)
        time.sleep(3)
        full_body_element = driver.find_element(By.TAG_NAME, "body")
        full_body_element.screenshot(f"output{pythonOutputCounter}.png")
        driver.quit()
        return {'cell_snapshot': f"output{pythonOutputCounter}.png", 'text_output': '\n'.join(text_outputs)}
    except Exception as e:
        tb = "".join(traceback.format_exception_only(type(e), e))
        tb = re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?', '', tb)
        tb = re.sub(r"-{2,}", "-", tb)
        return {'cell_snapshot': "Error running code", 'text_output': tb}
