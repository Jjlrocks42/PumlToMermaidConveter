import json
import re
from typing import Dict, List, Any
from collections import defaultdict

class InteractiveDiagramConverter:
    def __init__(self):
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, str]] = []
        self.package_hierarchy = defaultdict(set)
        
    def parse_class_definition(self, line: str) -> tuple:
        """Parse class definition line to extract name and type"""
        parts = line.split()
        if 'abstract class' in line:
            return parts[-1], 'abstract'
        elif 'interface' in line:
            return parts[1], 'interface'
        elif 'enum' in line:
            return parts[1], 'enum'
        else:
            return parts[1], 'class'

    def analyze_package_hierarchy(self, class_name: str):
        """Analyze and store package hierarchy"""
        package_parts = class_name.split('.')
        for i in range(1, len(package_parts)):
            parent_package = '.'.join(package_parts[:i])
            full_package = '.'.join(package_parts[:i+1])
            self.package_hierarchy[parent_package].add(full_package)

    def get_color_palette(self):
        """Provide a rich color palette for different package levels"""
        return {
            # Blues for different package depths
            1: [('#4a90e2', '#2171c7'), ('#5da5eb', '#3b8bd4'), ('#76b9f3', '#5aa0e0')],
            
            # Greens for deeper packages
            2: [('#7ed321', '#5ea018'), ('#8edc3c', '#6ec92a'), ('#a0e356', '#82cc3c')],
            
            # Oranges for even deeper packages
            3: [('#f5a623', '#d4840f'), ('#f7b043', '#e69422'), ('#f9bf63', '#f0a635')],
            
            # Purples for very deep packages
            4: [('#9013fe', '#7502d6'), ('#a533ff', '#8a19e6'), ('#b753ff', '#9f3bdc')],
            
            # Fallback for extremely deep or unknown packages
            'default': [('#666666', '#444444'), ('#777777', '#555555'), ('#888888', '#666666')]
        }

    def get_section_colors(self, class_name: str, class_type: str) -> tuple:
        """Determine colors based on package hierarchy and class type"""
        # Special handling for specific types
        if class_type == 'interface':
            return '#9013fe', '#7502d6'
        
        # Analyze package hierarchy
        self.analyze_package_hierarchy(class_name)
        
        # Determine package depth
        package_parts = class_name.split('.')
        depth = min(len(package_parts) - 1, 4)
        
        # Get color palette for this depth
        color_palette = self.get_color_palette().get(depth, self.get_color_palette()['default'])
        
        # Choose color based on a consistent hash of the full package name
        color_index = hash(class_name) % len(color_palette)
        
        return color_palette[color_index]

    def get_section_type(self, class_name: str) -> str:
        """Determine section type based on package structure"""
        # Split the package name into parts
        parts = class_name.lower().split('.')
        
        # Check for specific section indicators
        section_indicators = {
            'field_staff': ['staff', 'employee', 'worker', 'field'],
            'customer_facing': ['customer', 'client', 'user', 'service'],
            'common': ['common', 'shared', 'util', 'utility', 'base'],
            'config': ['config', 'configuration', 'settings']
        }
        
        # Check each part against section indicators
        for section, indicators in section_indicators.items():
            if any(indicator in part for part in parts for indicator in indicators):
                return section
        
        return 'other'

    def calculate_position(self, total_classes: int) -> dict:
        """Calculate positions for all classes across sections"""
        sections = {
            'field_staff': [],
            'customer_facing': [],
            'common': [],
            'config': [],
            'other': []
        }
        
        for class_name, _ in self.classes.items():
            section = self.get_section_type(class_name)
            sections[section].append(class_name)
        
        positions = {}
        section_x = {
            'field_staff': 100,
            'common': 400,
            'customer_facing': 700,
            'config': 250,
            'other': 550
        }
        
        spacing = 150
        
        for section, x in section_x.items():
            for index, class_name in enumerate(sections[section]):
                y = 100 + (index * spacing)
                positions[class_name] = {'x': x, 'y': y}
        
        return positions

    def parse_method(self, line: str) -> Dict[str, str]:
        """Parse method definition"""
        visibility = '+'
        match = re.match(r'([+\-#~])?(\w+)\s*\((.*?)\)', line.strip())
        if match:
            visibility = match.group(1) or '+'
            name = match.group(2)
            params = match.group(3)
            return {
                'name': name,
                'visibility': visibility,
                'params': f'({params})'
            }
        return None

    def parse_attribute(self, line: str) -> Dict[str, str]:
        """Parse attribute definition"""
        visibility = '+'
        match = re.match(r'([+\-#~])?\s*(\w+)', line.strip())
        if match:
            visibility = match.group(1) or '+'
            name = match.group(2)
            return {
                'name': name,
                'visibility': visibility
            }
        return None

    def parse_relationship(self, line: str) -> Dict[str, str]:
        """Parse relationship definition"""
        patterns = {
            r'([A-Za-z0-9._$]+)\s*(?:-+|\.+)(?:\|>|>)\s*([A-Za-z0-9._$]+)': 'inheritance',
            r'([A-Za-z0-9._$]+)\s*-+>\s*([A-Za-z0-9._$]+)': 'association',
            r'([A-Za-z0-9._$]+)\s*\*-+>\s*([A-Za-z0-9._$]+)': 'composition',
            r'([A-Za-z0-9._$]+)\s*o-+>\s*([A-Za-z0-9._$]+)': 'aggregation',
            r'([A-Za-z0-9._$]+)\s*\.\.->\s*([A-Za-z0-9._$]+)': 'dependency'
        }
        
        for pattern, rel_type in patterns.items():
            match = re.search(pattern, line)
            if match:
                return {
                    'source': match.group(1),
                    'target': match.group(2),
                    'type': rel_type
                }
        return None

    def convert_to_interactive(self, puml_code: str) -> dict:
        """Convert PlantUML to interactive diagram format"""
        self.classes.clear()
        self.relationships.clear()
        self.package_hierarchy.clear()
        
        current_class = None
        lines = puml_code.splitlines()
        
        # First pass: collect all classes
        for line in lines:
            line = line.strip()
            if line.startswith(('class ', 'interface ', 'enum ', 'abstract class ')):
                class_name, class_type = self.parse_class_definition(line)
                current_class = class_name
                
                # Assign colors
                if 'common' in class_name.lower() or 'poa.common' in class_name.lower():
                    bg_color, border_color = '#FF9900', '#CC6600'  # Orange for similar names or folders
                elif 'client' in class_name.lower() or 'customer' in class_name.lower():
                    bg_color, border_color = '#6666FF', '#4444CC'  # Blue for client/config classes
                elif 'config' in class_name.lower():
                    bg_color, border_color = '#4fedc8', '#4444CC'  # Blue for client/config classes
                elif 'mongo' in class_name.lower() or 'db' in class_name.lower():
                    bg_color, border_color = '#dded4f', '#4444CC'  # Blue for client/config classes
                elif 'pojo' in class_name.lower():
                    bg_color, border_color = '#ed4f74', '#4444CC'  # Blue for client/config classes
                elif 'dto' in class_name.lower() or 'poa.dto' in class_name.lower():
                    bg_color, border_color = '#ed894f', '#4444CC'  # Blue for client/config classes
                elif 'poa.exceptions' in class_name.lower():
                    bg_color, border_color = '#ed894f', '#4444CC'  # Blue for client/config classes
                elif 'poa.repositories' in class_name.lower():
                    bg_color, border_color = '#67098a', '#4444CC'  # Blue for client/config classes
                elif 'com.ge.enmac' in class_name.lower():
                    bg_color, border_color = '#ffb516', '#4444CC'  # Blue for client/config classes
                elif 'send' in class_name.lower():
                    bg_color, border_color = '#17f7ff', '#4444CC'  # Blue for client/config classes
                elif 'control' in class_name.lower():
                    bg_color, border_color = '#ff1f17', '#4444CC'  # Blue for client/config classes
                elif 'endpoint' in class_name.lower():
                    bg_color, border_color = '#ff17f7', '#4444CC'  # Blue for client/config classes
                else:
                    bg_color, border_color = '#666666', '#444444'  # Default gray
                
                self.classes[current_class] = {
                    'type': class_type,
                    'methods': [],
                    'attributes': [],
                    'description': f'{class_type.capitalize()} {class_name}',
                    'backgroundColor': bg_color,
                    'borderColor': border_color
                }
        
        # Second pass: process methods, attributes, and relationships
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith("'") or line.startswith("@"):
                continue
                
            if line.startswith(('class ', 'interface ', 'enum ', 'abstract class ')):
                class_name, _ = self.parse_class_definition(line)
                current_class = class_name
                continue
            
            relationship = self.parse_relationship(line)
            if relationship:
                self.relationships.append(relationship)
                continue
            
            if current_class and line not in ['{', '}']:
                line = line.strip("{ }").strip()
                if '(' in line and ')' in line:
                    method = self.parse_method(line)
                    if method:
                        self.classes[current_class]['methods'].append(method)
                else:
                    attribute = self.parse_attribute(line)
                    if attribute:
                        self.classes[current_class]['attributes'].append(attribute)
        
        # Calculate positions and finalize nodes and edges
        positions = self.calculate_position(len(self.classes))
        
        nodes = []
        edges = []
        
        for class_name, class_data in self.classes.items():
            # Neon green for standalone nodes
            if not any(rel['source'] == class_name or rel['target'] == class_name for rel in self.relationships):
                class_data['backgroundColor'] = '#39FF14'  # Neon green for standalone nodes
            
            node_data = {
                'id': class_name,
                'label': class_name.split('.')[-1],
                'type': class_data['type'],
                'methods': class_data['methods'],
                'attributes': class_data['attributes'],
                'description': class_data['description'],
                'backgroundColor': class_data['backgroundColor'],
                'borderColor': class_data['borderColor'],
                'position': positions.get(class_name, {'x': 400, 'y': 100})
            }
            nodes.append({'data': node_data})
        
        for rel in self.relationships:
            source_class = self.classes.get(rel['source'])
            edge_color = source_class['backgroundColor'] if source_class else '#666666'
            
            edges.append({
                'data': {
                    'source': rel['source'],
                    'target': rel['target'],
                    'type': rel['type'],
                    'color': edge_color,
                    'label': rel['type']
                }
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }

def convert_to_interactive_html(puml_code: str, template_path: str, output_path: str):
    """Convert PlantUML to interactive HTML diagram"""
    converter = InteractiveDiagramConverter()
    diagram_data = converter.convert_to_interactive(puml_code)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    marker = "const classData = {"
    split_point = template.find(marker)
    if split_point == -1:
        raise ValueError("Could not find insertion point in template")
    
    first_part = template[:split_point]
    second_part = template[split_point:]
    
    end_marker = "cy.add(classData.nodes);"
    end_point = second_part.find(end_marker)
    if end_point == -1:
        raise ValueError("Could not find end point in template")
    
    formatted_data = json.dumps(diagram_data, indent=8)
    html_content = (
        first_part +
        f"const classData = {formatted_data};\n\n        " +
        second_part[end_point:]
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)