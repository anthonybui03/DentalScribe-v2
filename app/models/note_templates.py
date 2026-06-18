"""Dental note templates — v2"""
import json
import os
from dataclasses import dataclass
from pathlib import Path

_TEMPLATES_FILE = (
    Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe-v2" / "templates.json"
)


@dataclass
class NoteTemplate:
    name: str
    llm_instruction: str
    skeleton: str
    builtin: bool = False


_BUILTINS = [
    NoteTemplate("Hygiene Recall", builtin=True,
        llm_instruction="Format the following dictation as a Hygiene Recall note. Include sections: Subjective, Oral Hygiene, Perio Assessment, Radiographs, Assessment, Plan, Provider Review.",
        skeleton="Subjective:\n\nOral Hygiene:\n\nPerio Assessment:\n\nRadiographs:\n\nAssessment:\n\nPlan:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Limited Exam", builtin=True,
        llm_instruction="Format the following dictation as a Limited Exam note. Include sections: Chief Complaint, Clinical Findings, Assessment, Plan, Provider Review.",
        skeleton="Chief Complaint:\n\nClinical Findings:\n\nAssessment:\n\nPlan:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Pediatric Restorative", builtin=True,
        llm_instruction="Format the following dictation as a Pediatric Restorative note. Include sections: Subjective, Behavior, Anesthesia, Treatment Completed, Post-op Instructions, Provider Review.",
        skeleton="Subjective:\n\nBehavior:\n\nAnesthesia:\n\nTreatment Completed:\n\nPost-op Instructions:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Fluoride / SDF", builtin=True,
        llm_instruction="Format the following dictation as a Fluoride Varnish or Silver Diamine Fluoride (SDF) note. Include: Teeth Treated, Material Applied, Concentration, Patient/Guardian Consent, Post-op Instructions, Provider Review.",
        skeleton="Teeth Treated:\n\nMaterial Applied:\n\nConcentration:\n\nPatient/Guardian Consent:\n\nPost-op Instructions:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Extraction", builtin=True,
        llm_instruction="Format the following dictation as an Extraction note. Include sections: Tooth/Teeth, Anesthesia, Procedure, Hemostasis, Complications, Post-op Instructions, Provider Review.",
        skeleton="Tooth/Teeth:\n\nAnesthesia:\n\nProcedure:\n\nHemostasis:\n\nComplications:\n\nPost-op Instructions:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Referral Letter", builtin=True,
        llm_instruction="Format the following dictation as a professional dental referral letter. Include: Date, Referring Provider, Patient Name, Reason for Referral, Clinical Summary, Requested Treatment, Provider Review.",
        skeleton="Date:\n\nReferring Provider:\n\nPatient (if stated):\n\nReason for Referral:\n\nClinical Summary:\n\nRequested Treatment:\n\nProvider Review: Required before chart entry.\n"),
    NoteTemplate("Custom / Freeform", builtin=True,
        llm_instruction="Convert the following dictation into a clean dental clinical note. Organize logically and include a Provider Review reminder at the end.",
        skeleton="Subjective:\n\nObjective:\n\nAssessment:\n\nPlan:\n\nProvider Review: Required before chart entry.\n"),
]

_registry: dict = {}


def load_templates():
    reg = {t.name: t for t in _BUILTINS}
    if _TEMPLATES_FILE.exists():
        try:
            for item in json.loads(_TEMPLATES_FILE.read_text(encoding="utf-8")):
                reg[item["name"]] = NoteTemplate(name=item["name"],
                    llm_instruction=item.get("llm_instruction",""),
                    skeleton=item.get("skeleton",""), builtin=False)
        except Exception as e:
            print(f"[templates] {e}")
    _registry.clear(); _registry.update(reg)
    return _registry


def save_custom_templates(templates):
    _TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TEMPLATES_FILE.write_text(json.dumps(
        [{"name":t.name,"llm_instruction":t.llm_instruction,"skeleton":t.skeleton}
         for t in templates if not t.builtin], indent=2), encoding="utf-8")


def get_registry():
    if not _registry: load_templates()
    return _registry

def get_template(name):
    reg = get_registry()
    return reg.get(name, reg.get("Custom / Freeform", _BUILTINS[-1]))

def template_names(): return list(get_registry().keys())

def add_or_update_template(t):
    reg = get_registry(); reg[t.name] = t
    save_custom_templates(list(reg.values()))

def delete_template(name):
    reg = get_registry(); t = reg.get(name)
    if not t or t.builtin: return False
    del reg[name]; save_custom_templates(list(reg.values())); return True


# Convenience aliases used by TemplatesWindow
TEMPLATES = get_registry()


def save_custom_template(name: str, skeleton: str) -> None:
    t = NoteTemplate(name=name,
                     llm_instruction="Format the following dictation as a professional dental chart note.",
                     skeleton=skeleton,
                     builtin=False)
    add_or_update_template(t)
    TEMPLATES.update(get_registry())


def delete_custom_template(name: str) -> None:
    delete_template(name)
    reg = get_registry()
    TEMPLATES.clear()
    TEMPLATES.update(reg)
