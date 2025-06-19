# transformer/course_transformer/course_helper_parsers/department_parser.py

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- STUB LOOKUP MAPS ---
# In a real implementation, this data would be loaded from a configuration file (e.g., a JSON or CSV).
# For now, we define them here as placeholders.

DEPT_NAME_TO_CODE_MAP = {
    "Accounting": "ACCT",
    "Agriculture": "AGR",
    "Agriculture, Honours": "AGRS",
    "Animal Biology": "ABIO",
    "Animal Science": "ANSC",
    "Anthropology": "ANTH",
    "Applied Geomatics": "AG",
    "Applied Human Nutrition": "AHN",
    "Art History": "ARTH",
    "Arts and Sciences": "AS",
    "Bio-Medical Science": "BIOM",
    "Biochemistry": "BIOC",
    "Biodiversity": "BIOD",
    "Biological and Medical Physics": "BMPH",
    "Biological and Pharmaceutical Chemistry": "BPCH",
    "Biological Engineering": "BIOE",
    "Biological Science": "BIOS",
    "Biology": "BIOL",
    "Biomedical Engineering": "BME",
    "Biomedical Toxicology": "BTOX",
    "Biotechnology": "BIOT",
    "Black Canadian Studies": "BLCK",
    "Business": "BUS",
    "Business Data Analytics": "BDA",
    "Business Economics": "BECN",
    "Chemical Physics": "CHPY",
    "Chemistry": "CHEM",
    "Child Studies": "CSTU",
    "Classical and Modern Cultures": "CMC",
    "Classical Studies": "CLAS",
    "Computer Engineering": "CENG",
    "Computer Science": "CS",
    "Computing and Information Science": "CIS",
    "Creative Arts, Health and Wellness": "CREA",
    "Creative Writing": "CW",
    "Criminal Justice and Public Policy": "CJPP",
    "Crop Science": "CRSC",
    "Culture and Technology Studies": "CTS",
    "Earth Observation and Geographic Information Science": "EO",
    "Ecology": "ECOL",
    "Economics": "ECON",
    "Engineering Systems and Computing": "ESC",
    "English": "ENGL",
    "Entrepreneurship": "ENT",
    "Environment and Resource Management": "ERM",
    "Environmental Citizenship": "ECT",
    "Environmental Conservation": "ECV",
    "Environmental Economics and Policy": "EEP",
    "Environmental Engineering": "ENVE",
    "Environmental Governance": "EGOV",
    "Environmental Management": "EM",
    "Environmental Sciences": "ENVS",
    "Equine Management": "EQM",
    "European Cultures": "EC",
    "Family and Child Studies": "FCS",
    "Family Studies and Human Development": "FSHD",
    "Food and Agricultural Business": "FAB",
    "Food Engineering": "FENG",
    "Food Science": "FOOD",
    "Food, Agricultural and Resource Economics": "FARE",
    "French Studies": "FREN",
    "Geography": "GEOG",
    "German": "GERM",
    "Government, Economics and Management": "GEM",
    "History": "HIST",
    "Horticulture": "HRT",
    "Hospitality and Tourism Management": "HTM",
    "Human Kinetics": "HK",
    "Human Resources": "HR",
    "Indigenous Environmental Governance": "IEG",
    "Indigenous Environmental Science and Practice": "IESP",
    "International Business": "IB",
    "International Development Studies": "IDS",
    "Italian": "ITAL",
    "Justice and Legal Studies": "JLS",
    "Landscape Architecture": "LA",
    "Leadership": "LEAD",
    "Linguistics": "LING",
    "Management": "MGMT",
    "Management Economics and Finance": "MEF",
    "Marine and Freshwater Biology": "MFB",
    "Marketing": "MKTG",
    "Marketing Management": "MKMN",
    "Mathematical Economics": "MAEC",
    "Mathematical Science": "MSCI",
    "Mathematics": "MATH",
    "Mechanical Engineering": "MECH",
    "Mechatronics Engineering": "MTE",
    "Media and Cinema Studies": "MCST",
    "Microbiology": "MICR",
    "Molecular Biology and Genetics": "MBG",
    "Museum Studies": "MS",
    "Music": "MUSC",
    "Nanoscience": "NANO",
    "Neuroscience": "NEUR",
    "Nutritional and Nutraceutical Sciences": "NANS",
    "One Health": "ONEH",
    "Organic Agriculture": "OAGR",
    "Philosophy": "PHIL",
    "Physical Science": "PSCI",
    "Physics": "PHYS",
    "Plant Science": "PLSC",
    "Political Science": "POLS",
    "Project Management": "PM",
    "Psychology": "PSYC",
    "Public Policy and Administration": "PPA",
    "Real Estate": "RE",
    "Restaurant and Beverage Management": "RBM",
    "Sexualities, Genders and Social Change": "SXGN",
    "Sociology": "SOC",
    "Software Engineering": "SENG",
    "Spanish and Hispanic Studies": "SPAH",
    "Sport and Event Management": "SPMT",
    "Statistics": "STAT",
    "Studio Art": "SART",
    "Sustainable Business": "SB",
    "Theatre Studies": "THST",
    "Theoretical Physics": "THPY",
    "Veterinary Medicine": "VM",
    "Water Resources Engineering": "WRE",
    "Wildlife Biology and Conservation": "WBC",
    "Zoology": "ZOO"
}

DEPT_NAME_TO_PARENT_NAME_MAP = {
    # College of Arts
    "Department of History": "College of Arts",
    "Department of Philosophy": "College of Arts",
    "School of English and Theatre Studies": "College of Arts",
    "School of Fine Art and Music": "College of Arts",
    "School of Languages and Literatures": "College of Arts",

    # College of Biological Science
    "Department of Integrative Biology": "College of Biological Science",
    "Department of Molecular and Cellular Biology": "College of Biological Science",
    "Department of Human Health and Nutritional Sciences": "College of Biological Science",

    # Gordon S. Lang School of Business and Economics
    "Department of Management": "Gordon S. Lang School of Business and Economics",
    "Department of Economics and Finance": "Gordon S. Lang School of Business and Economics",
    "Department of Marketing and Consumer Studies": "Gordon S. Lang School of Business and Economics",
    "School of Hospitality, Food and Tourism Management": "Gordon S. Lang School of Business and Economics",
    "Executive Programs": "Gordon S. Lang School of Business and Economics",

    # College of Engineering and Physical Sciences
    "Department of Chemistry": "College of Engineering and Physical Sciences",
    "School of Computer Science": "College of Engineering and Physical Sciences",
    "Department of Mathematics and Statistics": "College of Engineering and Physical Sciences",
    "Department of Physics": "College of Engineering and Physical Sciences",
    "School of Engineering": "College of Engineering and Physical Sciences",

    # College of Social and Applied Human Sciences
    "Department of Family Relations and Applied Nutrition": "College of Social and Applied Human Sciences",
    "Department of Geography, Environment and Geomatics": "College of Social and Applied Human Sciences",
    "Department of Psychology": "College of Social and Applied Human Sciences",
    "Department of Political Science": "College of Social and Applied Human Sciences",
    "Department of Sociology and Anthropology": "College of Social and Applied Human Sciences",
    "Guelph Institute of Development Studies": "College of Social and Applied Human Sciences",

    # Ontario Agricultural College
    "Department of Food, Agricultural and Resource Economics": "Ontario Agricultural College",
    "Department of Animal Biosciences": "Ontario Agricultural College",
    "School of Environmental Sciences": "Ontario Agricultural College",
    "Department of Food Science": "Ontario Agricultural College",
    "Department of Plant Agriculture": "Ontario Agricultural College",
    "School of Environmental Design and Rural Development": "Ontario Agricultural College",
    "Regional CampusesRidgetown Campus": "Ontario Agricultural College",

    # Ontario Veterinary College
    "Department of Biomedical Sciences": "Ontario Veterinary College",
    "Department of Clinical Studies": "Ontario Veterinary College",
    "Department of Pathobiology": "Ontario Veterinary College",
    "Department of Population Medicine": "Ontario Veterinary College"
}


def _generate_dept_id(dept_name: str) -> str:
    """Generates a consistent, unique ID from a name."""
    if not dept_name:
        return ""
    return f"dept_{dept_name.strip().lower().replace(' ', '_').replace('&', 'and')}"


def parse_department(dept_string: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parses a department string into a structured Department object using lookup maps."""
    if not isinstance(dept_string, str) or not dept_string.strip():
        return None

    dept_name = dept_string.strip()
    
    dept_code = DEPT_NAME_TO_CODE_MAP.get(dept_name)
    parent_name = DEPT_NAME_TO_PARENT_NAME_MAP.get(dept_name)
    parent_id = _generate_dept_id(parent_name) if parent_name else None

    department_obj = {
        "deptId": _generate_dept_id(dept_name),
        "name": dept_name,
        "code": dept_code,
        "parentId": parent_id
    }
    
    return department_obj