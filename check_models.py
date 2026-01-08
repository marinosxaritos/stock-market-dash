import google.generativeai as genai

# ΒΑΛΕ ΤΟ ΚΛΕΙΔΙ ΣΟΥ ΕΔΩ
GOOGLE_API_KEY = "AIzaSyCQqoBy1E_1Pp8bnk_nY3ccTURVoxtxrl0" 

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    print("Checking available models...")
    print("------------------------------------------------")
    
    found = False
    for m in genai.list_models():
        # Ψάχνουμε μοντέλα που μπορούν να παράγουν κείμενο (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            found = True
            
    print("------------------------------------------------")
    if not found:
        print("Δεν βρέθηκαν μοντέλα. Κάτι τρέχει με το κλειδί ή τη βιβλιοθήκη.")
        
except Exception as e:
    print(f"Error: {e}")