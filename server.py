from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import google.generativeai as genai
import json
import os
import concurrent.futures # Για παράλληλη εκτέλεση (Ταχύτητα!)
import time 
from dotenv import load_dotenv # Χρειάζεται: pip install python-dotenv

# IMPORT ΤΗ ΔΙΚΗ ΣΟΥ ΛΙΣΤΑ (Βεβαιώσου ότι το αρχείο market_symbols.py υπάρχει)
from market_symbols import TOP_100

# Φόρτωση περιβάλλοντος από το .env αρχείο
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- 1. ΡΥΘΜΙΣΗ GEMINI ---
# ΠΡΟΣΟΧΗ: Στο .env αρχείο σου πρέπει να έχεις: GOOGLE_API_KEY=το_κλειδι_σου
# Αντί για VITE_API_URL, προτείνω να το ονομάσεις GOOGLE_API_KEY για να είναι ξεκάθαρο ότι είναι backend secret.
GOOGLE_API_KEY = os.getenv("VITE_API_URL")

if not GOOGLE_API_KEY:
    print("--> ⚠️ WARNING: Δεν βρέθηκε GOOGLE_API_KEY στο .env file!")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-flash-latest')
        print("--> Gemini AI Configured Successfully!")
    except Exception as e:
        print(f"--> Warning: Gemini AI setup failed: {e}")

# --- ΒΟΗΘΗΤΙΚΗ ΣΥΝΑΡΤΗΣΗ ΓΙΑ THREADING ---
# Αυτή η συνάρτηση τρέχει παράλληλα για κάθε μετοχή
def fetch_stock_data(symbol):
    try:
        clean_symbol = symbol.strip().upper()
        # Χρησιμοποιούμε Ticker για μεμονωμένη κλήση (μέσα στο thread)
        stock = yf.Ticker(clean_symbol)
        
        # Το fast_info είναι πολύ πιο γρήγορο από το .info
        price = stock.fast_info.last_price
        prev_close = stock.fast_info.previous_close
        market_cap = stock.fast_info.market_cap
        
        # Αν η yahoo δεν δώσει τιμή, αγνοούμε τη μετοχή
        if price is None or prev_close is None:
            return None
            
        change = ((price - prev_close) / prev_close) * 100
        
        return {
            "symbol": clean_symbol, 
            "name": clean_symbol, # Το fast_info δεν έχει πάντα το longName, κρατάμε το σύμβολο για ταχύτητα
            "price": price, 
            "changesPercentage": change, 
            "marketCap": market_cap
        }
    except Exception:
        # Αν αποτύχει μία μετοχή, δεν "σκάει" η εφαρμογή, απλά επιστρέφει None
        return None

# --- ENDPOINT 1: ΤΙΜΕΣ (Parallel Optimized) ---
@app.route('/api/quote', methods=['GET'])
def get_quote():
    start_time = time.time()
    symbols_arg = request.args.get('symbols', '')
    
    if symbols_arg:
        # Search: Ο χρήστης ψάχνει κάτι συγκεκριμένο
        symbols_list = symbols_arg.split(',')
    else:
        # Homepage: Παίρνουμε τις πρώτες 30 από τη λίστα
        symbols_list = TOP_100[:30]

    print(f"--> Ζητάω τιμές για {len(symbols_list)} μετοχές (Parallel)...")
    
    data = []
    
    # Χρήση ThreadPoolExecutor για ταυτόχρονη λήψη δεδομένων
    # max_workers=10 σημαίνει ότι ανοίγει 10 "κανάλια" ταυτόχρονα
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_stock_data, symbols_list))

    # Φιλτράρουμε τα αποτελέσματα για να βγάλουμε τα None (errors)
    data = [r for r in results if r is not None]
        
    # Ταξινόμηση με βάση το Market Cap
    data.sort(key=lambda x: x['marketCap'] or 0, reverse=True)
    
    print(f"--> Ολοκληρώθηκε σε {time.time() - start_time:.2f} seconds")
    return jsonify(data)

# --- ENDPOINT 2: DEEP ANALYSIS (AI) ---
@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        req_data = request.json
        symbol = req_data.get('symbol')
        print(f"--> Deep Analyzing {symbol}...")
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="3mo")
        
        def get_safe(key, default=0):
            val = info.get(key, default)
            return val if val is not None else default

        peg_ratio = get_safe('pegRatio', None)
        if peg_ratio is None:
            fwd_pe = get_safe('forwardPE')
            growth = get_safe('earningsGrowth')
            if fwd_pe and growth and growth > 0:
                peg_ratio = round(fwd_pe / (growth * 100), 2)
            else:
                peg_ratio = "N/A"

        current_price = get_safe('currentPrice')
        raw_trend = hist['Close'].tail(5).tolist() if not hist.empty else []
        recent_trend = [float(round(x, 2)) for x in raw_trend]

        financial_data = {
            "Symbol": symbol,
            "Price": current_price,
            "Sector": info.get('sector', 'Unknown'),
            "Description": info.get('longBusinessSummary', '')[:500],
            "Valuation": {
                "Trailing PE": get_safe('trailingPE', 'N/A'), 
                "PEG": peg_ratio
            },
            "Analysts": {
                "Target": get_safe('targetMeanPrice', 'N/A'), 
                "Rec": info.get('recommendationKey', 'N/A')
            },
            "Technical": {
                "200 Day MA": float(get_safe('twoHundredDayAverage')),
                "Trend": recent_trend
            }
        }

        prompt = f"""
        Ενέργησε ως Senior Investment Analyst. Κάνε μια επενδυτική έκθεση για τη μετοχή **{symbol}**.
        ΔΕΔΟΜΕΝΑ: {json.dumps(financial_data)}
        
        Ακολούθησε ΑΥΣΤΗΡΑ αυτή τη δομή (Markdown):
        ## 1. 🏢 Εισαγωγή
        - Τι κάνει η εταιρεία; ({info.get('sector', 'N/A')})
        ## 2. 🛡️ Οικονομική Υγεία & Valuation
        - Είναι φθηνή; (P/E, PEG).
        ## 3. 🔮 Πρόβλεψη & Στόχοι
        - Στόχος Τιμής: ${financial_data['Analysts']['Target']} (Τρέχουσα: ${current_price}).
        ## 4. 📉 Τεχνική Εικόνα
        - Τάση 5 ημερών: {recent_trend}.
        ## 5. 🎲 Σενάρια (Bear/Bull)
        
        # 🎯 ΣΥΜΠΕΡΑΣΜΑ: [BUY / HOLD / SELL]
        Δικαιολόγησε σε 2 προτάσεις.
        """

        response = model.generate_content(prompt)
        return jsonify({"analysis": response.text})

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- ENDPOINT 3: ΛΕΠΤΟΜΕΡΕΙΕΣ ΜΕΤΟΧΗΣ ΓΙΑ SIDEBAR ---
@app.route('/api/details', methods=['GET'])
def get_details():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
        
    print(f"--> Φέρνω λεπτομέρειες για {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        details = {
            "symbol": symbol,
            "name": info.get('longName', symbol),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "description": info.get('longBusinessSummary', 'No description available.'),
            "price": info.get('currentPrice', 0),
            "currency": info.get('currency', 'USD'),
            "dayHigh": info.get('dayHigh', 0),
            "dayLow": info.get('dayLow', 0),
            "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh', 0),
            "fiftyTwoWeekLow": info.get('fiftyTwoWeekLow', 0),
            "volume": info.get('volume', 0),
            "marketCap": info.get('marketCap', 0),
            "peRatio": info.get('trailingPE', 'N/A'),
            "dividendYield": info.get('dividendYield', 'N/A'),
            "beta": info.get('beta', 'N/A')
        }
        return jsonify(details)
    except Exception as e:
        print(f"Details Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    # --- ENDPOINT 4: ΙΣΤΟΡΙΚΟ ΤΙΜΩΝ ΓΙΑ CHART ---
@app.route('/api/history', methods=['GET'])
def get_history():
    symbol = request.args.get('symbol')
    period = request.args.get('period', '1mo') # default 1 μήνας
    
    # Επιτρεπτά periods για το yfinance: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    valid_periods = ['1mo', '3mo', '6mo', '1y', 'max']
    if period not in valid_periods:
        period = '1mo'

    try:
        ticker = yf.Ticker(symbol)
        # Παίρνουμε ιστορικό (μόνο κλείσιμο μας νοιάζει για απλό chart)
        hist = ticker.history(period=period)
        
        # Μετατροπή σε λίστα
        data = []
        for date, row in hist.iterrows():
            data.append({
                # Μορφή ημερομηνίας: "Jan 05" ή "2023-01-05"
                "date": date.strftime('%d %b'), 
                "price": round(row['Close'], 2)
            })
            
        return jsonify(data)
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/financials', methods=['GET'])
def get_financials():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    print(f"--> Fetching financials for {symbol}...")

    try:
        ticker = yf.Ticker(symbol)
        
        # 1. Παίρνουμε τα δεδομένα
        financials = ticker.financials
        
        # 2. ΑΝΤΙΜΕΤΩΠΙΣΗ ΤΟΥ ERROR "NaN": 
        # Λέμε στο Pandas να αντικαταστήσει όλα τα NaN με 0.
        # Αυτό λύνει το JSON error απευθείας.
        financials = financials.fillna(0)

        if financials.empty:
            return jsonify([])

        data = []
        cols = financials.columns

        for date in cols:
            try:
                year = date.strftime('%Y')
                
                # Helper για να βρούμε τη σωστή γραμμή (Revenue/Income)
                # Ψάχνουμε αν υπάρχει κάποιο από αυτά τα ονόματα στο index
                def get_row_value(df, possible_names, col_date):
                    for name in possible_names:
                        if name in df.index:
                            return df.loc[name, col_date]
                    return 0

                # Λίστες με πιθανά ονόματα (βάσει yfinance docs & common keys)
                revenue_keys = ['Total Revenue', 'Operating Revenue', 'Revenue', 'Total Net Sales']
                income_keys = ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing Ops']

                # Παίρνουμε τις τιμές (τώρα είμαστε σίγουροι ότι δεν είναι NaN)
                revenue = get_row_value(financials, revenue_keys, date)
                income = get_row_value(financials, income_keys, date)

                data.append({
                    "year": year,
                    "revenue": float(revenue), # Το κάνουμε float για σιγουριά
                    "netIncome": float(income)
                })

            except Exception as e:
                print(f"Error parsing year {date}: {e}")
                continue
        
        # Ταξινόμηση ώστε να πηγαίνει από παλιά -> νέα (για το γράφημα)
        data.sort(key=lambda x: x['year'])
        
        return jsonify(data)

    except Exception as e:
        print(f"Financials Error: {e}")
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    print("Server running on port 5000... (THREADED MODE)")
    app.run(debug=True, port=5000)