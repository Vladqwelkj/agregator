import os
from datetime import datetime
from flask import Flask, render_template
from binance.client import Client
from datetime import datetime


app = Flask(__name__)


def get_symbols():
    symbols = os.listdir('datasets/')
    symbols.sort()
    return symbols


@app.route('/')
def hello_world():
    symbols = get_symbols()
    return render_template('index.html', symbols=symbols, symbols_amount=len(symbols))

@app.route('/<datatype>/<symbol>')
def log(datatype=None, symbol=None):
    content = open('datasets/'+symbol+'/'+datatype+'.txt', 'r').read()
    if 'ohlcv' in datatype:
        content = content.split('\n')
        for ind, row in enumerate(content):
            if len(row.split(' ')) < 4:
                continue
            dt = '<b>'+str(datetime.utcfromtimestamp(int(row[:10])))+'</b>'
            content[ind] = dt + row[10:]

        content = '<br>'.join(content)
    else:
        values = content.split(' ')
        values[0] = '<b>'+str(datetime.utcfromtimestamp(int(values[0])))+'</b>'
        content = ' '.join(values)
    return '<b>datetime UTC(upload time) - values</b><br>'+content


if __name__=='__main__':
    app.run('0.0.0.0', '5050')
