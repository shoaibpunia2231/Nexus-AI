"""
chatbot_service.py -- Context-aware clinical education chatbot.
Answers patient questions regarding blood parameters, dengue risk, warning signs,
and explains current session values safely without claiming to diagnose.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ClinicalChatbot:
    """
    Intelligent context-aware assistant for patient education and report interpretation.
    Adheres strictly to medical safety guardrails:
    - Never issues a definitive diagnosis
    - Never recommends dangerous NSAIDs
    - Emphasizes red-flag symptoms and professional physician consultation
    """

    SYSTEM_DISCLAIMER = (
        "⚠️ *Medical Notice: I am an AI educational assistant, not a doctor. "
        "This information is for clinical screening and educational purposes only "
        "and does not replace medical diagnosis by a qualified physician.*"
    )

    @classmethod
    def get_response(
        cls,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Processes user query in the context of their current uploaded report / screening.
        Uses local clinical reasoning engine, or delegates to Gemini/OpenAI if configured.
        """
        msg = user_message.strip().lower()
        ctx = context or {}
        patient = ctx.get("patient", {})
        params = ctx.get("parameters", {})
        prediction = ctx.get("prediction", {})

        # Check for external LLM configuration if configured
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        if gemini_key:
            llm_resp = cls._call_gemini(user_message, ctx, chat_history, gemini_key)
            if llm_resp:
                return llm_resp
        elif openai_key:
            llm_resp = cls._call_openai(user_message, ctx, chat_history, openai_key)
            if llm_resp:
                return llm_resp

        # Local intelligent clinical reasoning engine (reliable, instant, private)
        return cls._local_clinical_reasoning(msg, patient, params, prediction)

    @classmethod
    def _local_clinical_reasoning(
        cls, msg: str, patient: dict, params: dict, prediction: dict
    ) -> str:
        # 1. Direct questions about current patient session values
        # Platelet count questions
        if any(w in msg for w in ["my platelet", "my platelets", "platelet count in my report", "what was my platelet"]):
            plt = params.get("platelet_count")
            if plt is not None:
                status = "low" if float(plt) < 150000 else "within normal limits"
                warning = (
                    " Below 100,000 cells/µL is a key dengue alert sign; below 50,000 requires urgent emergency medical monitoring."
                    if float(plt) < 100000
                    else " The standard reference range is 150,000 to 450,000 cells/µL."
                )
                return (
                    f"According to your current report, your **Platelet Count** is **{int(float(plt)):,} cells/µL**, "
                    f"which is {status}.{warning}\n\n{cls.SYSTEM_DISCLAIMER}"
                )
            return "No platelet count has been extracted or confirmed in this session yet. Please upload a report or enter it in the form."

        # Haemoglobin questions
        if any(w in msg for w in ["my haemoglobin", "my hemoglobin", "my hb", "what was my haemoglobin"]):
            hb = params.get("haemoglobin")
            if hb is not None:
                val = float(hb)
                status = "low" if val < 12.0 else ("elevated" if val > 17.5 else "normal")
                return (
                    f"Your recorded **Haemoglobin (Hb)** is **{val:.1f} g/dL** (Reference: 12.0 – 17.5 g/dL), which is considered **{status}**.\n\n"
                    f"In dengue, elevated haemoglobin combined with dropping platelets can be a sign of haemoconcentration (plasma leakage).\n\n"
                    f"{cls.SYSTEM_DISCLAIMER}"
                )
            return "Haemoglobin has not been recorded in the current session yet."

        # PDW questions
        if any(w in msg for w in ["my pdw", "what was my pdw", "what is my pdw"]):
            pdw = params.get("pdw")
            if pdw is not None:
                val = float(pdw)
                status = "elevated" if val > 17.0 else "within normal range"
                return (
                    f"Your recorded **PDW (Platelet Distribution Width)** is **{val:.1f}%** (Reference: 9.0 – 17.0%), which is **{status}**.\n\n"
                    f"PDW measures variation in platelet sizes. Elevated PDW indicates active platelet turnover or destruction, which frequently occurs during viral infections like dengue.\n\n"
                    f"{cls.SYSTEM_DISCLAIMER}"
                )
            return "PDW is not recorded yet in this session."

        # Explain my results / all blood test results
        if any(w in msg for w in ["explain my", "my blood test", "explain results", "what do my results mean", "summary of my"]):
            if params and any(params.get(k) is not None for k in ["platelet_count", "haemoglobin", "pdw"]):
                plt = params.get("platelet_count")
                hb = params.get("haemoglobin")
                pdw = params.get("pdw")
                risk = prediction.get("risk_level", "Pending screening")
                prob = prediction.get("probability")

                lines = ["Here is a summary of your evaluated parameters:"]
                if plt is not None:
                    lines.append(f"• **Platelet Count:** {int(float(plt)):,} cells/µL ({'⚠️ Below normal' if float(plt) < 150000 else '✅ Normal'})")
                if hb is not None:
                    lines.append(f"• **Haemoglobin:** {float(hb):.1f} g/dL")
                if pdw is not None:
                    lines.append(f"• **PDW:** {float(pdw):.1f}%")

                if risk != "Pending screening":
                    lines.append(f"\n**AI Screening Assessment:** **{risk} Risk**" + (f" ({round(float(prob)*100, 1)}% probability)" if prob else ""))
                    lines.append(f"*{prediction.get('message', '')}*")

                lines.append(f"\n{cls.SYSTEM_DISCLAIMER}")
                return "\n".join(lines)
            return "No blood test parameters are currently loaded. Upload your blood report or fill in the questionnaire to get started!"

        # 2. General educational questions
        # What is platelet count
        if "platelet" in msg or "plt" in msg:
            return (
                "**What are Platelets?**\n\n"
                "Platelets (thrombocytes) are blood cell fragments essential for blood clotting and stopping bleeding.\n\n"
                "• **Normal Reference Range:** 150,000 – 450,000 cells/µL.\n"
                "• **In Dengue:** The dengue virus can suppress bone marrow production and accelerate destruction of platelets, leading to thrombocytopenia (low platelet count).\n"
                "• **Warning Level:** Platelets below 100,000 cells/µL require close clinical observation; below 50,000 cells/µL requires emergency hospital care.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # What is haemoglobin
        if "haemoglobin" in msg or "hemoglobin" in msg or "hb" in msg:
            return (
                "**What is Haemoglobin (Hb)?**\n\n"
                "Haemoglobin is the iron-rich protein in red blood cells that transports oxygen throughout the body.\n\n"
                "• **Normal Range:** 12.0 – 17.5 g/dL (varies slightly by sex and age).\n"
                "• **Why it matters in Dengue:** A sudden rise in haemoglobin (haemoconcentration) often occurs alongside plasma leakage—a hallmark of severe dengue where blood volume decreases due to fluid leaking out of capillaries into tissues.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # What is PDW
        if "pdw" in msg:
            return (
                "**What is PDW (Platelet Distribution Width)?**\n\n"
                "PDW measures the variation in the sizes of circulating platelets.\n\n"
                "• **Normal Range:** 9.0 – 17.0% (or fL depending on laboratory analyzer).\n"
                "• **Significance:** A high PDW indicates that platelets differ markedly in volume (anisocytosis). In dengue, as mature platelets are destroyed, the bone marrow releases larger, immature platelets, leading to increased PDW.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # Danger signs / when to visit hospital
        if any(w in msg for w in ["hospital", "doctor", "emergency", "danger", "warning sign", "worse"]):
            return (
                "🚨 **Dengue Red-Flag Warning Signs (Seek Immediate Hospital Care):**\n\n"
                "1. **Bleeding:** Bleeding from gums, nose, vomit, or black/tarry stools.\n"
                "2. **Severe Abdominal Pain:** Intense persistent stomach pain or tenderness.\n"
                "3. **Persistent Vomiting:** Inability to keep fluids down (at least 3 times in 24 hours).\n"
                "4. **Extreme Lethargy or Restlessness:** Sudden confusion, severe weakness, or fainting.\n"
                "5. **Fluid Accumulation:** Swelling in hands, feet, or puffiness in face.\n"
                "6. **Platelets dropping rapidly** or falling below 50,000 cells/µL.\n\n"
                "Please do not delay seeking medical attention at an emergency room or hospital if any of these are present.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # Diet / hydration / home care
        if any(w in msg for w in ["diet", "food", "drink", "water", "hydration", "papaya", "kiwi", "eat"]):
            return (
                "💧 **Hydration & Nutritional Care During Dengue:**\n\n"
                "• **Fluid Intake:** Drink 2.5 to 3 Litres of fluids daily. Water, ORS (Oral Rehydration Salts), tender coconut water, and clear broths help restore lost electrolytes.\n"
                "• **Platelet Supportive Foods:** Papaya leaf extract, kiwi, pomegranate, and Vitamin C rich fruits are commonly used as dietary support.\n"
                "• **Light Meals:** Porridge, boiled vegetables, and soups are easy on the stomach.\n"
                "• **AVOID:** Spicy, greasy, or deep-fried foods.\n"
                "• ⚠️ **CRITICAL MEDICATION SAFETY:** Never take **Aspirin, Ibuprofen, or other NSAIDs**, as they impair platelet function and increase severe bleeding risks. Only Paracetamol under medical guidance should be used for fever.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # Dengue transmission / contagious
        if any(w in msg for w in ["contagious", "spread", "mosquito", "transmit", "how do you get"]):
            return (
                "🦟 **How is Dengue Spread?**\n\n"
                "Dengue is **not contagious** from person to person through casual contact, saliva, or air.\n\n"
                "It is transmitted solely through the bite of an infected female **Aedes mosquito** (primarily *Aedes aegypti* and *Aedes albopictus*), which typically bites during the early morning and late afternoon.\n\n"
                "Prevention focuses on preventing mosquito bites and eliminating standing water where mosquitoes breed.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # Can you diagnose me / Do I have dengue?
        if any(w in msg for w in ["do i have dengue", "diagnose me", "am i positive", "confirm dengue"]):
            risk = prediction.get("risk_level")
            msg_part = f"Based on your blood test parameters, the ML model calculated a **{risk} Risk** assessment." if risk else "Please run the screening tool to view an AI risk assessment."
            return (
                f"**Clinical Diagnostic Notice:**\n\n"
                f"{msg_part}\n\n"
                f"However, **an AI model cannot diagnose dengue**. A definitive medical diagnosis requires specific laboratory testing ordered by a medical professional:\n"
                f"• **NS1 Antigen Test** (detectable in the first 1–5 days of fever)\n"
                f"• **Dengue IgM/IgG Antibody ELISA** (usually positive after day 5)\n"
                f"• **RT-PCR** for viral RNA\n\n"
                f"Please consult a certified medical practitioner for diagnosis and treatment.\n\n"
                f"{cls.SYSTEM_DISCLAIMER}"
            )

        # Default fallback
        return (
            "I'm here to help you understand your blood test parameters, explain dengue risk factors, "
            "and provide guidance on symptoms to watch out for.\n\n"
            "You can ask me questions like:\n"
            "• *\"What was my platelet count?\"*\n"
            "• *\"Explain my blood test results\"*\n"
            "• *\"What does low platelet count mean?\"*\n"
            "• *\"What are the warning signs to go to the hospital?\"*\n"
            "• *\"What foods and fluids help during recovery?\"*\n\n"
            f"{cls.SYSTEM_DISCLAIMER}"
        )

    @classmethod
    def _call_gemini(cls, message: str, context: dict, history: list, api_key: str) -> Optional[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                f"You are Nexus AI Health Assistant, an educational AI chatbot. "
                f"You provide clear, empathetic, medically accurate education about dengue, blood tests, and symptoms. "
                f"CRITICAL SAFETY RULE: You are NOT a doctor and must NEVER provide a definitive diagnosis or replace professional medical care. "
                f"Always warn against NSAIDs (aspirin/ibuprofen). Always emphasize hospital evaluation for warning signs.\n\n"
                f"Patient Session Context: {context}\n\n"
                f"User: {message}"
            )
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text + f"\n\n{cls.SYSTEM_DISCLAIMER}"
        except Exception as e:
            logger.warning(f"Gemini API call error: {e}")
        return None

    @classmethod
    def _call_openai(cls, message: str, context: dict, history: list, api_key: str) -> Optional[str]:
        # Optional OpenAI fallback if key provided
        return None
