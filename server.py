from flask import Flask, render_template, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os

app = Flask(__name__)

# ------------------------------------- Webdriver Setup -----------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1440,900")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
url = 'https://web.sensibull.com/option-chain'
driver.get(url)

# Setting up selenium constants and basic imports & functions
bynam = By.NAME
byxpt = By.XPATH
bycss = By.CSS_SELECTOR
bylnk = By.LINK_TEXT
bytag = By.TAG_NAME

def check_exists_by_xpath(xpath):
    try:
        driver.find_element(byxpt, xpath)
    except NoSuchElementException:
        return False
    return True

@app.route('/')
def refreshData():
    driver.refresh()
    colHeads = ["calls_oi_change", "calls_oi", "calls_ltp", "strike", "iv", "puts_ltp", "puts_oi", "puts_oi_change"]
    finalData = []
    table = driver.find_element(byxpt, '//div[@id="oc-table-body"]')
    rowGroups = table.find_elements(byxpt, 'div[@class="rt-tr-group"]')
    counter = 1
    for row in rowGroups:
        rowData = None
        columns = None
        if (counter % 2) != 0:
            rowData = row.find_element(byxpt, 'div[@class="rt-tr -odd"]')
        else:
            rowData = row.find_element(byxpt, 'div[@class="rt-tr -even"]')
            
        colVals = []
        
        columns = rowData.find_elements(byxpt, 'div[@class="rt-td"]')
        colLength = len(columns)
        reverseCounter = colLength - 1
        for col in columns:
            currentColIteration = colLength - reverseCounter
            if currentColIteration == 1 or currentColIteration == 8:
                if col.text == '-':
                    colVals.append('0%')
                    continue
            colVals.append(col.text)
            reverseCounter -= 1
        
        if len(colVals):
            finalData.append(dict(zip(colHeads, colVals)))
        else:
            print('No values found!')
            return
        counter += 1
    
    # Finding the index of maximum calls_oi value
    max_calls_oi_index = -1
    max_calls_oi_value = float('-inf')

    for i, data in enumerate(finalData):
        calls_oi = data['calls_oi']
        try:
            calls_oi_float = float(calls_oi)
            if calls_oi_float > max_calls_oi_value:
                max_calls_oi_index = i
                max_calls_oi_value = calls_oi_float
        except ValueError:
            continue
            
    if max_calls_oi_index == -1:
        # Handle case where no valid calls_oi value was found
        print("No valid calls_oi value found!")
        return
    else:
        start_index = max_calls_oi_index - 2
        end_index = max_calls_oi_index + 5
        filteredData = finalData[start_index:end_index]

    # ------------------------------------- OI Comparision Graph -----------------------------------

    # Extracting data for plotting
    strike_values = [int(d['strike']) for d in filteredData]
    calls_oi_values = [float(d['calls_oi']) for d in filteredData]
    puts_oi_values = [float(d['puts_oi']) for d in filteredData]

    # Creating the figure and axis objects
    fig, ax = plt.subplots()

    # Setting x-axis values and labels
    x = range(len(filteredData))
    ax.set_xticks(x)
    ax.set_xticklabels(strike_values)

    # Plotting the bars
    bar_width = 0.35
    ax.bar(x, calls_oi_values, width=bar_width, label='calls_oi')
    ax.bar([i + bar_width for i in x], puts_oi_values, width=bar_width, label='puts_oi')

    # Adding labels and titles
    ax.set_xlabel('Strike')
    ax.set_ylabel('OI')
    ax.set_title('Calls OI and Puts OI')
    ax.legend()

    # Adding values inside the bars
    for i, v in enumerate(calls_oi_values):
        ax.text(i, v, str(v), ha='center', va='bottom')
    for i, v in enumerate(puts_oi_values):
        ax.text(i + bar_width, v, str(v), ha='center', va='bottom')

    # Saving the graph as an image file
    graph_filename = 'oi_comparison_graph.png'
    graph_path = os.path.join(app.root_path, 'static', graph_filename)
    plt.savefig(graph_path)
    plt.close()

    # ------------------------------------- OI Percenatage Change Graph -----------------------------------

    # Extracting data for plotting
    strike_values = [int(d['strike']) for d in filteredData]
    calls_oi_change_values = [float(d['calls_oi_change'].strip('%')) for d in filteredData]
    puts_oi_change_values = [float(d['puts_oi_change'].strip('%')) for d in filteredData]

    # Creating the figure and axis objects
    fig, ax = plt.subplots()

    # Setting x-axis values and labels
    x = range(len(filteredData))
    ax.set_xticks(x)
    ax.set_xticklabels(strike_values)

    # Plotting the bars
    ax.bar(x, calls_oi_change_values, width=bar_width, label='calls_oi_change')
    ax.bar([i + bar_width for i in x], puts_oi_change_values, width=bar_width, label='puts_oi_change')

    # Adding labels and titles
    ax.set_xlabel('Strike')
    ax.set_ylabel('OI Change (%)')
    ax.set_title('Calls OI Change and Puts OI Change')
    ax.legend()

    # Adding values inside the bars
    for i, v in enumerate(calls_oi_change_values):
        va = 'bottom' if v >= 0 else 'top'
        ax.text(i, v, str(v), ha='center', va=va)
    for i, v in enumerate(puts_oi_change_values):
        va = 'bottom' if v >= 0 else 'top'
        ax.text(i + bar_width, v, str(v), ha='center', va=va)

    # Saving the graph as an image file
    oi_change_graph_filename = 'oi_change_graph.png'
    oi_change_graph_path = os.path.join(app.root_path, 'static', oi_change_graph_filename)
    plt.savefig(oi_change_graph_path)
    plt.close()

    return render_template('index.html', graph_filename=graph_filename, oi_change_graph_filename=oi_change_graph_filename)

if __name__ == '__main__':
    app.run()
