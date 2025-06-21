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
    "Agricultural & Resource Economics": "FARE",  # Added
    "Agricultural and Resource Economics": "FARE",  # Added
    "Animal Biology": "ABIO",
    "Animal Science": "ANSC",
    "Anthropology": "ANTH",
    "Applied Geomatics": "AG",
    "Applied Human Nutrition": "AHN",
    "Art History": "ARTH",
    "Arts and Sciences": "ASCI",  # Official code is ASCI
    "Associate VP Academic": None,  # Added (administrative office)
    "Bio-Medical Science": "BIOM",
    "Biomedical Science": "BIOM",  # Added
    "Biochemistry": "BIOC",
    "Biodiversity": "BIOD",
    "Biological and Medical Physics": "BMPH",
    "Biological and Pharmaceutical Chemistry": "BPCH",
    "Biological Engineering": "BIOE",
    "Biological Science": "BIOS",
    "Biology": "BIOL",
    "Biomedical Engineering": "BME",
    "Biomedical Toxicology": "TOX",  # Official code is TOX
    "Biotechnology": "BIOT",
    "Black Canadian Studies": "BLCK",
    "Business": "BUS",
    "Business Administration": "BUS",  # Added
    "Business Data Analytics": "BDA",
    "Business Economics": "BECN",
    "Chemical Physics": "CHPY",
    "Chemistry": "CHEM",
    "Child Studies": "CSTU",
    "Classical and Modern Cultures": "CMC",
    "Classical Studies": "CLAS",
    "Computer Engineering": "CENG",
    "Computer Science": "CS",
    "School of Computer Science": "CS",
    "Computing and Information Science": "CIS",
    "Creative Arts, Health and Wellness": "CREA",
    "Creative Writing": "CRWR",  # Official code is CRWR
    "Criminal Justice and Public Policy": "CJPP",
    "Crop Science": "CROP",  # Official code is CROP
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
    "European Studies": "EURO",  # Official code is EURO
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
    "Horticulture": "HORT",  # Official code is HORT
    "Hospitality and Tourism Management": "HTM",
    "Human Kinetics": "HK",
    "Human Resources": "HR",
    "Indigenous Environmental Governance": "IEG",
    "Indigenous Environmental Science and Practice": "IESP",
    "International Business": "IB",
    "International Development Studies": "IDEV",  # Official code is IDEV
    "Italian": "ITAL",
    "Justice and Legal Studies": "JLS",
    "Landscape Architecture": "LARC",  # Official code is LARC
    "Leadership": "LEAD",
    "Linguistics": "LING",
    "Management": "MGMT",
    "Department of Management": "MGMT",
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
    "Plant Science": "PLNT",  # Official code is PLNT
    "Political Science": "POLS",
    "Project Management": "PM",
    "Psychology": "PSYC",
    "Public Policy and Administration": "PPA",
    "Real Estate": "REAL",  # Official code is REAL
    "Restaurant and Beverage Management": "RBM",
    "Sexualities, Genders and Social Change": "SXGN",
    "Sociology": "SOC",
    "Software Engineering": "SENG",
    "Spanish and Hispanic Studies": "SPAN",  # Official code is SPAN
    "Sport and Event Management": "SPMT",
    "Statistics": "STAT",
    "Studio Art": "SART",
    "Sustainable Business": "SB",
    "Theatre Studies": "THST",
    "Theoretical Physics": "THPY",
    "Veterinary Medicine": "VETM",  # Official code is VETM
    "Water Resources Engineering": "WRE",
    "Wildlife Biology and Conservation": "WBC",
    "Zoology": "ZOO",
    "Department of Animal Biosciences": "ANSC",  # From source data
    "Department of Economics and Finance": "ECON",  # From source data
    "Department of Marketing and Consumer Studies": "MKTG",  # From source data
}


# --- UPDATED Parent ID Lookup Map ---
# This map has been expanded with the "Areas of Study" and other subjects.
DEPT_NAME_TO_PARENT_NAME_MAP = {
    # College of Arts
    "School of Theatre, English, and Creative Writing": "College of Arts",
    "Department of History": "College of Arts",
    "History": "College of Arts",
    "Department of Philosophy": "College of Arts",
    "Philosophy": "College of Arts",
    "School of English and Theatre Studies": "College of Arts",
    "English": "College of Arts",
    "Creative Writing": "College of Arts",
    "Theatre Studies": "College of Arts",
    "Media and Cinema Studies": "College of Arts",
    "School of Fine Art and Music": "College of Arts",
    "Art History": "College of Arts",
    "Music": "College of Arts",
    "Studio Art": "College of Arts",
    "Museum Studies": "College of Arts",
    "School of Languages and Literatures": "College of Arts",
    "Classical Studies": "College of Arts",
    "European Cultures": "College of Arts",
    "French Studies": "College of Arts",
    "German": "College of Arts",
    "Italian": "College of Arts",
    "Linguistics": "College of Arts",
    "Spanish and Hispanic Studies": "College of Arts",
    "Black Canadian Studies": "College of Arts",

    # College of Biological Science
    "Department of Integrative Biology": "College of Biological Science",
    "Biodiversity": "College of Biological Science",
    "Marine and Freshwater Biology": "College of Biological Science",
    "Wildlife Biology and Conservation": "College of Biological Science",
    "Zoology": "College of Biological Science",
    "Department of Molecular and Cellular Biology": "College of Biological Science",
    "Biochemistry": "College of Biological Science",
    "Microbiology": "College of Biological Science",
    "Molecular Biology and Genetics": "College of Biological Science",
    "Department of Human Health and Nutritional Sciences": "College of Biological Science",
    "Applied Human Nutrition": "College of Biological Science",
    "Human Kinetics": "College of Biological Science",
    "Nutritional and Nutraceutical Sciences": "College of Biological Science",
    "Bio-Medical Science": "College of Biological Science",
    "Biology": "College of Biological Science",
    "Biological Science": "College of Biological Science",
    "Biomedical Science": "Ontario Veterinary College",  # Added

    # Gordon S. Lang School of Business and Economics
    "Department of Management": "Gordon S. Lang School of Business and Economics",
    "Management": "Gordon S. Lang School of Business and Economics",
    "Human Resources": "Gordon S. Lang School of Business and Economics",
    "International Business": "Gordon S. Lang School of Business and Economics",
    "Leadership": "Gordon S. Lang School of Business and Economics",
    "Project Management": "Gordon S. Lang School of Business and Economics",
    "Sustainable Business": "Gordon S. Lang School of Business and Economics",
    "Department of Economics and Finance": "Gordon S. Lang School of Business and Economics",
    "Economics": "Gordon S. Lang School of Business and Economics",
    "Management Economics and Finance": "Gordon S. Lang School of Business and Economics",
    "Mathematical Economics": "Gordon S. Lang School of Business and Economics",
    "Business Economics": "Gordon S. Lang School of Business and Economics",
    "Department of Marketing and Consumer Studies": "Gordon S. Lang School of Business and Economics",
    "Marketing": "Gordon S. Lang School of Business and Economics",
    "Marketing Management": "Gordon S. Lang School of Business and Economics",
    "Public Policy and Administration": "Gordon S. Lang School of Business and Economics",
    "Real Estate": "Gordon S. Lang School of Business and Economics",
    "School of Hospitality, Food and Tourism Management": "Gordon S. Lang School of Business and Economics",
    "Hospitality and Tourism Management": "Gordon S. Lang School of Business and Economics",
    "Restaurant and Beverage Management": "Gordon S. Lang School of Business and Economics",
    "Sport and Event Management": "Gordon S. Lang School of Business and Economics",
    "Executive Programs": "Gordon S. Lang School of Business and Economics",
    "Accounting": "Gordon S. Lang School of Business and Economics",
    "Government, Economics and Management": "Gordon S. Lang School of Business and Economics",
    "Business Administration": "Gordon S. Lang School of Business and Economics",  # Added

    # ... (other existing mappings unchanged) ...
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
