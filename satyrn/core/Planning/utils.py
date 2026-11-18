'''
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
'''

import re
from typing import List, Dict

def oxfordcomma(items: List[str]) -> str:
    """
    Joins the list of items as a comma separated list with proper use of "and".
    :param items: Items to put into the statement.
    :type items: List of str
    :return: A string representing the properly formatted list.
    :rtype: str
    """
    # TODO: Move this function to the utils file
    if len(items) == 0:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + ' and ' + items[1]
    return ', '.join(items[:-1]) + ', and ' + items[-1]

def capitalize_first_only(s: str) -> str:
    """
    Capitalizes the first letter of the string.
    :param s: The string to capitalize.
    :type s: str
    :return: A string with the first letter capitalized.
    :rtype: str
    """
    return s[0].upper() + s[1:]

def extract_slots(s: str) -> List[str]:
    """
    Extracts the slots from the given string.
    :param slot: A SQR slot of the form {<slot_type>[<slot_ref>]}
    :type slot: str
    :return: A list of all slots.
    :rtype: str
    """
    return re.findall(r'{[^{}]+(?=})}', s)

def intersect_lists(lst_of_lst: List[List],) -> List:
    """
    Compute the intersection of the elements of all given lists
    :param lst_of_lst: The list of lists to find the intersection over
    :type lst_of_lst: List of List
    :return: The list of values contained in all lists
    :rtype: List
    """
    sets = map(set, lst_of_lst)
    return list(set.intersection(*sets))

def is_slot(s: str) -> bool:
    """
    Determines if the given string is a slot or not.
    :param s: The string to check.
    :type s: str
    :return: True or False depending if the given string is a slot
    :rtype: bool
    """
    return len(extract_slots(s)) == 1

def remove_extra_whitespace(s: str) -> str:
    """
    Removes all extra whitespace in a given string.
    :param s: The string to remove extra whitespace from.
    :type s: str
    :return: A copy of the string with all extra whitespace removed.
    :rtype: str
    """
    return " ".join(s.split())

def analysis_steps_to_json(steps: Dict[str, 'AnalysisStep']) -> Dict:
    return {
        k: str(v) for k, v in steps.items()
    }

def get_reference_attributes(entity_reference_template: str) -> List[str]:
    """
    Extracts the list of attribute names that occur in the given entity reference template.
    :param entity_reference_template: The entity reference template to find the attributes for.
    :type entity_reference_template: str
    :return: The list of attribute names that occur in the given entity reference template.
    :rtype: List[str]
    """
    return re.findall(r'\{(\w+)\}', entity_reference_template)