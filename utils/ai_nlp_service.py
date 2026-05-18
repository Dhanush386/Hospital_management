import os
import json
import google.generativeai as genai

def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[!] GEMINI_API_KEY not found in environment.")
        return False
    
    genai.configure(api_key=api_key)
    return True

def generate_soap_note_from_transcript(transcript):
    """
    Takes a raw doctor consultation transcript (e.g. from Whisper)
    and converts it into a structured SOAP JSON format using Gemini.
    """
    if not setup_gemini():
        return _fallback_mock_note(transcript)

    prompt = f"""
    You are an expert clinical AI assistant. Given the following rough voice transcription
    from a doctor's consultation, extract and structure the information into a standard 
    SOAP format (Subjective, Objective, Assessment, Plan).

    Format the output strictly as a JSON object with these keys:
    - "subjective": (string) What the patient describes (symptoms, history).
    - "objective": (string) What the doctor observes or measures (vitals, exams).
    - "assessment": (string) The clinical diagnosis or condition.
    - "plan": (string) Recommended treatments, medicines, tests, and follow-ups.

    Transcription:
    "{transcript}"
    
    Return ONLY valid JSON. Do not include markdown formatting like ```json.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up in case the model returns markdown blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        soap_json = json.loads(response_text.strip())
        return soap_json
    except Exception as e:
        print(f"[!] Gemini AI error: {e}")
        return _fallback_mock_note(transcript)

def _fallback_mock_note(transcript):
    """Fallback if API fails or key is missing"""
    return {
        "subjective": f"Patient reported: {transcript[:50]}...",
        "objective": "Pending clinical observations.",
        "assessment": "Pending diagnosis.",
        "plan": "1. Rest\n2. Follow up if symptoms persist."
    }
