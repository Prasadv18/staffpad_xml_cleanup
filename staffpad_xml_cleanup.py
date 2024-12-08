#!/usr/bin/env python3
# Author: Prasad Vidhyabaskaran

from lxml import etree as ET
from collections import OrderedDict, Counter
from xmldiff import main, formatting
import argparse
import pprint

class InstrumentManager:
    """
    Manages the renaming and standardization of instrument names in a MusicXML document.

    Attributes:
        instrument_swap_map (OrderedDict): Mapping of instrument names to their standardized names.
        instrument_rename_dict (dict): Mapping of instrument IDs to their renamed details.
        part_rename_dict (dict): Mapping of part IDs to their renamed details.
        instrument_counter (Counter): Tracks occurrences of each instrument for unique numbering.
        part_counter (Counter): Tracks occurrences of each part for unique numbering.
    """
    def __init__(self,tree):
        """
        Initializes the InstrumentManager with default mappings and counters.
        """
        self.tree = tree
        self.root = tree.getroot()
        
        self.instrument_swap_map = self._create_instrument_swap_map()
        self.instrument_rename_dict = {}
        self.part_rename_dict = {}
        self.instrument_counter = Counter()
        self.part_counter = Counter()

    def _create_instrument_swap_map(self):
        """
        Creates a mapping for standardizing instrument names.

        Returns:
            OrderedDict: A map of instrument names to their standardized counterparts.
        """        
        swap_map = OrderedDict()
        # Define mappings by sections
        sections = {
            "wind": ["Piccolo", "Alto Flute", "Bass Flute", "Flutes", "Flute",
                     "Oboes", "Oboe", "English Horn", "Contrabass Clarinet",
                     "Bass Clarinet", "Eb Clarinet", "Clarinets", "Clarinet",
                     "Contrabassoon", "Bassoons", "Bassoon", "Cor Anglais"],
            "horn": ["12 French Horns", "2 French Horns", "4 French Horns"],
            "brass": ["Horn Ensemble", "CineBrass French Horn", "2 Trumpets",
                      "Trumpet Ensemble", "Trumpet", "Bass Trombone", "Trombones",
                      "Trombone Ensemble", "Trombone", "Tuba"],
            "percussion": ["Timpani", "Cymbals", "Glockenspiel", "Marimba",
                           "Vibraphone", "Bass Drum 36in", "Bowed Gongs"],
            "keys" : ["Harp"],
            "voice": ["Sopranos", "Full Chorus", "Boys Choir", "Solo Soprano"],
            "strings": ["Violin 1", "Violin 2", "Viola", "Cello", "Bass",
                        "Violins 1", "Violins 2", "Violas", "Cellos", "Basses"],
        }
        
        for section, instruments in sections.items():
            for instrument in instruments:
                swap_map[instrument] = instrument

        # Add specific mappings
        swap_map["Cor Anglais"] = "English Horn"

        for i in range(1, 5):
            swap_map[f"Berlin Brass Horn {i}"] = "French Horn"
        swap_map["Horn Ensemble"] = "4 French Horns"
        swap_map["CineBrass French Horn"] = "French Horn"            
        swap_map["Trumpet Ensemble"] = "2 Trumpets"
        swap_map["Trombone Ensemble"] = "Trombones"

        for perc_inst in sections["percussion"]:
            swap_map[f"CinePerc {perc_inst}"] = perc_inst

        for voice_inst in sections["voice"]:
            swap_map[f"VOXOS {voice_inst}"] = voice_inst

        for string_inst in ["Violin 1", "Violin 2", "Viola", "Cello", "Bass"]:
            swap_map[f"Cinestrings Solo {string_inst}"] = f"Solo {string_inst}"
        for string_inst in ["Violin 1", "Violin 2", "Viola", "Cello", "Bass"]:
            swap_map[f"Cinestrings Solo {string_inst}"] = f"Solo {string_inst}"
            swap_map[f"First Chair {string_inst}"] = f"Solo {string_inst}"
        for string_inst in ["Violins 1", "Violins 2", "Violas", "Cellos", "Basses"]:
            swap_map[f"Berlin Strings {string_inst}"] = string_inst
        swap_map["Spitfire Chamber Strings Violins I"] = "Violins 1"
        swap_map["Spitfire Chamber Strings Violins II"] = "Violins 2"
        for string_inst in ["Violas", "Cellos", "Basses"]:
            swap_map[f"Spitfire Chamber Strings {string_inst}"] = string_inst

        return swap_map
    
    
    def _find_generic_name(self, name, counter):
        """
        Finds and generates a generic name for an instrument or part.

        Args:
            name (str): Original name of the instrument or part.
            counter (Counter): Counter for ensuring unique numbering.

        Returns:
            dict: A mapping with the original and renamed instrument or part name.
        """
        for instrument in self.instrument_swap_map.keys():
            if instrument in name:
                swap_name = self.instrument_swap_map[instrument]
                counter[swap_name] += 1
                numbered_swap_name = f"{swap_name} {counter[swap_name]}"
                return {"original name": name, "swap name": numbered_swap_name}
        return None

    def find_generic_instrument_names(self, root):
        """
        Finds and standardizes instrument names within the MusicXML document.

        Args:
            root (Element): Root element of the MusicXML document.
        """
        part_list = root.find('part-list')
        for score_part in part_list.findall('score-part'):
            part_id = score_part.get('id')
            for part_name in score_part.findall('part-name'):
                rename_map = self._find_generic_name(part_name.text, self.part_counter)
                if rename_map:
                    self.part_rename_dict[part_id] = rename_map

            for score_instrument in score_part.findall('score-instrument'):
                instrument_id = score_instrument.get('id')
                rename_map = self._find_generic_name(
                    score_instrument.find('instrument-name').text, self.instrument_counter)
                if rename_map:
                    self.instrument_rename_dict[instrument_id] = rename_map


            
    def _rename_element(self, element, rename_dict, tag_name):
        """
        Renames an XML element based on a rename mapping.

        Args:
            element (Element): XML element to rename.
            rename_dict (dict): Mapping for renaming elements.
            tag_name (str): Tag name to look for renaming.
        """
        element_id = element.get('id')
        rename_map = rename_dict.get(element_id)
        if rename_map:
            for tag in element.findall(tag_name):
                assert tag.text == rename_map['original name'], "Original name mismatch"
                tag.text = rename_map['swap name']
            
    def rename_instruments(self, root):
        """
        Renames instruments and parts in the MusicXML document.

        Args:
            root (Element): Root element of the MusicXML document.
        """
        
        part_list = root.find('part-list')
        for score_part in part_list.findall('score-part'):
            self._rename_element(score_part, self.part_rename_dict, 'part-name')
            for score_instrument in score_part.findall('score-instrument'):
                self._rename_element(score_instrument, self.instrument_rename_dict, 'instrument-name')

    def cleanup_names(self):
        """
        Cleans up naming by removing unnecessary numbering for single occurrences.
        """
        self._cleanup(self.instrument_counter, self.instrument_rename_dict)
        self._cleanup(self.part_counter, self.part_rename_dict)

    def _cleanup(self, counter, rename_dict):
        """
        Cleans up a rename dictionary by removing numbering for unique names.

        Args:
            counter (Counter): Counter of occurrences.
            rename_dict (dict): Rename dictionary to clean up.
        """
        for swap_name, count in counter.items():
            if count == 1:
                numbered_swap_name = f"{swap_name} 1"
                for element_id, rename_map in rename_dict.copy().items():
                    if rename_map and rename_map['swap name'] == numbered_swap_name:
                        rename_map['swap name'] = swap_name


    def dump_rename_map(self):
        pprint.pprint(self.part_rename_dict)
        pprint.pprint(self.instrument_rename_dict)

    def process_xml(self):
        self.find_generic_instrument_names(self.root)
        self.cleanup_names()
        self.rename_instruments(self.root)
        
    def write_xml(self,output_file):
        self.tree.write(output_file)        
        
class XMLUtility:
    @staticmethod
    def node_to_string(node):
        parts = []
        if node.tag:
            parts.append(f"tag: {node.tag}")
        if node.text and node.text.strip():
            parts.append(f"text: {node.text.strip()}")
        if node.attrib:
            parts.append(f"attrib: {node.attrib}")
        return ' '.join(parts)

    @staticmethod
    def print_work(tree):
        root = tree.getroot()

        for work in root.iter('work'):
            print(XMLUtility.node_to_string(work))
            for work_title in work.iter('work-title'):
                print(XMLUtility.node_to_string(work_title))

    @staticmethod
    def print_score_parts(root):
        part_list = root.find('part-list')
        for score_part in part_list.findall('score-part'):
            print("#-----------#")
            print(XMLUtility.node_to_string(score_part))
            for score_part_child in score_part:
                print(XMLUtility.node_to_string(score_part_child))
            for score_instrument in score_part.findall('score-instrument'):
                print(f"instrument-name:{score_instrument.find('instrument-name').text}")
                print(f"instrument-abbreviation:{score_instrument.find('instrument-abbreviation').text}")
                print(f"instrument-sound:{score_instrument.find('instrument-sound').text}")

    @staticmethod
    def diff_parts(root, part_rename_dict):
        measures_dict = {}
        for part in root.findall('part'):
            part_id = part.get('id')
            if "Flute" in part_rename_dict[part_id]['swap name']:
                print(f"{part_id} contains Flute")
                measures_dict[part_id] = []
            else:
                continue

            for measure in part.findall('measure'):
                measures_dict[part_id].append(measure)

        compare_parts = list(measures_dict.keys())
        for i_measure, measure in enumerate(measures_dict[compare_parts[0]]):
            measure_part_a = measure
            measure_part_b = measures_dict[compare_parts[1]][i_measure]
            diff = main.diff_trees(measure_part_a, measure_part_b, formatter=simple_formatter)
            if diff:
                print(f'measure {i_measure} differs')
                print(diff)






def main():
    parser = argparse.ArgumentParser(description='Takes a music xml file from Staffpad. Renames part and instrument names in a generic way to help with import into other programs like Dorico')
    parser.add_argument('--input_file', help='input xml file',required=True)
    args = parser.parse_args()

    output_file=args.input_file[:-4]+"_xml_cleanup.xml" #modified.xml"
    tree = ET.parse(args.input_file)
    inst_mgr = InstrumentManager(tree)
    xml_util = XMLUtility()
    xml_util.print_work(tree)        
    #print(inst_mgr.instrument_swap_map)
    #xml_util.print_score_parts(root)
    inst_mgr.process_xml()
    inst_mgr.write_xml(output_file)
    #pprint.pprint(inst_mgr.part_rename_dict)
    inst_mgr.dump_rename_map()


if __name__ == "__main__":
    main()



