import json
import sys
import os
import argparse
import re
from tqdm import tqdm
import html

import InteractiveDiagramConverter


# Add this at the top of your Python file, after the imports

TEMPLATE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Interactive Class Diagram</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape-pdf/0.3.0/cytoscape.pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
     <script src="https://cdnjs.cloudflare.com/ajax/libs/vue/3.4.15/vue.global.min.js"></script>
    <style>
        #cy {
            width: 100%;
            height: 800px;
            position: absolute;
            top: 0px;
            left: 0px;
        }

        .section-label {
            position: absolute;
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid #ccc;
        }

        #field-staff-label {
            top: 20px;
            left: 50px;
            color: #4a90e2;
        }

        #common-label {
            top: 20px;
            left: 45%;
            color: #7ed321;
        }

        #customer-facing-label {
            top: 20px;
            right: 50px;
            color: #f5a623;
        }


        #toolbar{
                    position: absolute;
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid #ccc;
            visibility: hidden;
        }

    </style>
</head>
<body>
    <div>
        <nav id="toolbar">
            <button id="export-png">Export to PNG</button>
            <button id="export-pdf">Export to PDF</button>
        </nav>
    </div>
    <div></div>
    <div id="field-staff-label" class="section-label">Field Staff</div>
    <div id="common-label" class="section-label">Common Components</div>
    <div id="customer-facing-label" class="section-label">Customer Facing</div>
    <div id="cy"></div>

    <script>
    
        const layoutConfig = {
            name: 'preset',
            padding: 50,
            spacingFactor: 1.5,
            animate: true,
            animationDuration: 500,
            fit: true
        };

        const nodeStyle = [{
            selector: 'node',
            style: {
                'shape': 'rectangle',
                'background-color': 'data(backgroundColor)',
                'border-color': 'data(borderColor)',
                'border-width': 2,
                'width': 'label',
                'height': 'label',
                'padding': '20px',
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '14px',
                'font-weight': 'bold',
                'text-wrap': 'wrap',
                'text-max-width': 200
            }
        }, {
            selector: 'edge',
            style: {
                'width': 2,
                'line-color': 'data(color)',
                'target-arrow-color': 'data(color)',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'font-size': '12px',
                'text-rotation': 'autorotate',
                'text-margin-y': -10
            }
        }, {
            selector: 'node[type="interface"]',
            style: {
                'border-style': 'dashed'
            }
        }];

        // Initialize cytoscape
        const cy = cytoscape({
            container: document.getElementById('cy'),
            elements: [],
            style: nodeStyle,
            layout: layoutConfig,
            wheelSensitivity: 0.2
        });

        // Add the class data
        const classData = {
            // This will be populated by the Python script
        };

        // Add nodes and edges
        cy.add(classData.nodes);
        cy.add(classData.edges);

        // Function to organize nodes into sections
        function organizeNodesIntoSections() {
            const fieldStaffY = 100;
            const commonY = 100;
            const customerFacingY = 100;
            const verticalSpacing = 150; // 1.5rem converted to pixels

            const fieldStaffNodes = cy.nodes().filter(node => 
                node.data('label').toLowerCase().startsWith('field') || 
                node.data('label').toLowerCase().startsWith('staff')
            );
            
            const customerFacingNodes = cy.nodes().filter(node => 
                node.data('label').toLowerCase().startsWith('customer') || 
                node.data('label').toLowerCase().startsWith('client')
            );
            
            const commonNodes = cy.nodes().filter(node => 
                node.data('label').toLowerCase().startsWith('common') || 
                node.data('label').toLowerCase().startsWith('shared')
            );

            // Position field staff nodes
            fieldStaffNodes.forEach((node, index) => {
                node.position({
                    x: 200,
                    y: fieldStaffY + (index * verticalSpacing)
                });
            });

            // Position common nodes
            commonNodes.forEach((node, index) => {
                node.position({
                    x: cy.width() / 2,
                    y: commonY + (index * verticalSpacing)
                });
            });

            // Position customer facing nodes
            customerFacingNodes.forEach((node, index) => {
                node.position({
                    x: cy.width() - 200,
                    y: customerFacingY + (index * verticalSpacing)
                });
            });
        }

        // Apply the organization after the graph is loaded
        cy.ready(() => {
            organizeNodesIntoSections();
            cy.fit();
            cy.center();
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            cy.fit();
            cy.center();
        });



        document.getElementById('export-png').addEventListener('click', () => {
            const pngContent = cy.png();
            const link = document.createElement('a');
            link.href = pngContent;
            link.download = 'diagram.png';
            link.click();
        });

        document.getElementById('export-pdf').addEventListener('click', async () => {
                try {
                    // Create a canvas with the diagram
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    // Set canvas size to match diagram
                    const { w, h } = cy.png({ scale: 2, full: true });
                    canvas.width = w;
                    canvas.height = h;
                    
                    // Create an image from the PNG
                    const img = new Image();
                    img.onload = () => {
                        ctx.drawImage(img, 0, 0);
                        
                        // Convert to PDF
                        const imgData = canvas.toDataURL('image/png');
                        const pdf = new jspdf.jsPDF({
                            orientation: 'landscape',
                            unit: 'px',
                            format: [w, h]
                        });
                        pdf.addImage(imgData, 'PNG', 0, 0, w, h);
                        pdf.save('diagram.pdf');
                    };
                    img.src = cy.png({ scale: 2, full: true });
                } catch (error) {
                    console.error('PDF Export failed:', error);
                    alert('Failed to export PDF. Check console for details.');
                }
            });

    </script>
    <script>

            function saveLayout() {
            const positions = {};
            cy.nodes().forEach(node => {
                positions[node.id()] = node.position();
            });
            localStorage.setItem('diagramLayout', JSON.stringify(positions));
            alert('Layout saved successfully!');
        }

        function loadLayout() {
            const savedLayout = localStorage.getItem('diagramLayout');
            if (savedLayout) {
                const positions = JSON.parse(savedLayout);
                cy.nodes().forEach(node => {
                    const pos = positions[node.id()];
                    if (pos) {
                        node.position(pos);
                    }
                });
                cy.fit(); // Adjust view to fit the loaded layout
                alert('Layout loaded successfully!');
            } else {
                alert('No saved layout found!');
            }
        }


        document.getElementById('export-png').addEventListener('click', () => {
            try {
                const pngContent = cy.png({
                    scale: 2,  // Higher resolution
                    full: true  // Capture entire graph
                });
                const link = document.createElement('a');
                link.href = pngContent;
                link.download = 'diagram.png';
                link.click();
            } catch (error) {
                console.error('PNG Export failed:', error);
                alert('Failed to export PNG. Check console for details.');
            }
        });

        document.getElementById('export-pdf').addEventListener('click', async () => {
        try {
            // Create a canvas with the diagram
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size to match diagram
            const { w, h } = cy.png({ scale: 2, full: true });
            canvas.width = w;
            canvas.height = h;
            
            // Create an image from the PNG
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0);
                
                // Convert to PDF
                const imgData = canvas.toDataURL('image/png');
                const pdf = new jspdf.jsPDF({
                    orientation: 'landscape',
                    unit: 'px',
                    format: [w, h]
                });
                pdf.addImage(imgData, 'PNG', 0, 0, w, h);
                pdf.save('diagram.pdf');
            };
            img.src = cy.png({ scale: 2, full: true });
        } catch (error) {
            console.error('PDF Export failed:', error);
            alert('Failed to export PDF. Check console for details.');
        }
    });

        // Keyboard shortcut for export
        document.addEventListener('keydown', async (event) => {
            // Check for Ctrl+Shift+E
            if (event.ctrlKey && event.shiftKey && event.key === 'E') {
                event.preventDefault();  // Prevent default browser behavior

                // Create a custom export dialog
                const exportDialog = document.createElement('div');
                exportDialog.innerHTML = `
                    <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                background: white; border: 2px solid #333; padding: 20px; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 1000;">
                        <h3>Export Diagram</h3>
                        <button id="export-png-dialog" style="margin: 10px; padding: 10px;">PNG</button>
                        <button id="export-pdf-dialog" style="margin: 10px; padding: 10px;">PDF</button>
                        <button id="save-layout-dialog" style="margin: 10px; padding: 10px;">Save Layout</button>
                        <button id="load-layout-dialog" style="margin: 10px; padding: 10px;">Load Layout</button>
                        <button id="cancel-export" style="margin: 10px; padding: 10px;">Cancel</button>
                    </div>
                `;
                document.body.appendChild(exportDialog);

                // Export PNG
                document.getElementById('export-png-dialog').addEventListener('click', () => {
                    try {
                        const pngContent = cy.png({
                            scale: 2,  // Higher resolution
                            full: true  // Capture entire graph
                        });
                        const link = document.createElement('a');
                        link.href = pngContent;
                        link.download = 'diagram.png';
                        link.click();
                        document.body.removeChild(exportDialog);
                    } catch (error) {
                        console.error('PNG Export failed:', error);
                        alert('Failed to export PNG. Check console for details.');
                    }
                });

                // Export PDF
                document.getElementById('export-pdf-dialog').addEventListener('click', async () => {
                    try {
                        const pdfContent = await cytoscape.exporters.pdf(cy, {
                            scale: 2,
                            full: true
                        });
                        const blob = new Blob([pdfContent], { type: 'application/pdf' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = 'diagram.pdf';
                        link.click();
                        document.body.removeChild(exportDialog);
                    } catch (error) {
                        console.error('PDF Export failed:', error);
                        alert('Failed to export PDF. Check console for details.');
                    }
                });

                  // Save Layout
                    document.getElementById('save-layout-dialog').addEventListener('click', () => {
                        saveLayout();
                        document.body.removeChild(exportDialog);
                    });

                    // Load Layout
                    document.getElementById('load-layout-dialog').addEventListener('click', () => {
                        loadLayout();
                        document.body.removeChild(exportDialog);
                    });

                // Cancel button
                document.getElementById('cancel-export').addEventListener('click', () => {
                    document.body.removeChild(exportDialog);
                });
            }
            
        });
    </script>
</body>
</html>"""





class DiagramConverter:
    def __init__(self):
        self.relationship_patterns = {
            r'([A-Za-z0-9._$]+)\s*(?:-+|\.+)(?:\|>|>)\s*([A-Za-z0-9._$]+)': r'\1 --|> \2',  # Inheritance
            r'([A-Za-z0-9._$]+)\s*(?:-+|\.+)(?:\|>|>)\s*([A-Za-z0-9._$]+)\s*:\s*(.+)': r'\1 --|> \2 : \3',  # Inheritance with label
            r'([A-Za-z0-9._$]+)\s*-+>\s*([A-Za-z0-9._$]+)': r'\1 --> \2',  # Association
            r'([A-Za-z0-9._$]+)\s*\*-+>\s*([A-Za-z0-9._$]+)': r'\1 --* \2',  # Composition
            r'([A-Za-z0-9._$]+)\s*o-+>\s*([A-Za-z0-9._$]+)': r'\1 --o \2',  # Aggregation
            r'([A-Za-z0-9._$]+)\s*\.\.->\s*([A-Za-z0-9._$]+)': r'\1 ..> \2',  # Dependency
            r'([A-Za-z0-9._$]+)\s*<-+\s*([A-Za-z0-9._$]+)': r'\2 --> \1',  # Reverse association
        }
        
        self.modifiers = {
            'abstract': '<<abstract>>',
            'interface': '<<interface>>',
            'enum': '<<enumeration>>',
            'static': '$',
            'abstract class': 'class',
        }
        
        self.MAX_DIAGRAM_SIZE = 5000
        self.current_size = 0
        self.diagram_count = 1
        self.defined_classes = set()

    def sanitize_class_name(self, name):
        """Sanitize class names to be Mermaid-compatible"""
        # Remove any package paths and special characters
        clean_name = name.split('.')[-1]  # Take only the class name, not the full path
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '', clean_name)
        return clean_name

    def format_method_signature(self, method_line):
        """Format method signatures to Mermaid syntax"""
        # Remove any special characters that could cause syntax errors
        method_line = re.sub(r'[<>"]', '', method_line)
        
        is_static = '{static}' in method_line
        method_line = method_line.replace('{static}', '')
        
        match = re.match(r'([+\-#~]?\s*)(.*?)\s*\((.*?)\)', method_line)
        if not match:
            return method_line
        
        visibility, name, params = match.groups()
        visibility = visibility.strip() if visibility else '+'
        if not visibility in ['+', '-', '#', '~']:
            visibility = '+'
            
        if is_static:
            visibility = visibility + '$'
        
        # Simplify parameters and remove special characters
        if params:
            params = re.sub(r'[^\w\s,]', '', params)
            param_parts = params.split(',')
            if len(param_parts) > 2:
                params = f"{param_parts[0].strip()}..."
            else:
                params = ', '.join(p.strip() for p in param_parts)
        
        return f"{visibility}{name}({params})"

    def format_attribute(self, attr_line):
        """Format class attributes to Mermaid syntax"""
        # Remove any special characters that could cause syntax errors
        attr_line = re.sub(r'[<>"]', '', attr_line)
        
        is_static = '{static}' in attr_line
        attr_line = re.sub(r'\{(?!static\})[^}]*\}', '', attr_line)
        attr_line = attr_line.replace('{static}', '').strip()
        
        match = re.match(r'([+\-#~]?\s*)(.*)', attr_line)
        if not match:
            return attr_line
        
        visibility, name = match.groups()
        visibility = visibility.strip() if visibility else '+'
        if not visibility in ['+', '-', '#', '~']:
            visibility = '+'
            
        if is_static:
            visibility = visibility + '$'
            
        # Clean up the name and remove type information
        name = name.strip().split()[-1]
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        
        return f"{visibility}{name}"

    def start_new_diagram(self, diagram_num):
        """Start a new diagram with proper syntax"""
        return [
            "classDiagram",
            "    direction TB"  # Changed to top-to-bottom for better readability
        ]

    def convert_class_diagram(self, puml_code):
        lines = puml_code.splitlines()
        total_lines = len(lines)
        mermaid_diagrams = []
        current_diagram = self.start_new_diagram(self.diagram_count)
        current_class = None
        self.defined_classes = set()
        
        with tqdm(total=total_lines, desc="Converting diagram") as pbar:
            i = 0
            while i < total_lines:
                line = lines[i].strip()
                pbar.update(1)
                
                if not line or line.startswith("'") or line.startswith("@"):
                    i += 1
                    continue
                
                current_size = sum(len(l) + 1 for l in current_diagram)
                
                if current_size > self.MAX_DIAGRAM_SIZE:
                    # Ensure all classes are defined before relationships
                    current_diagram = self.organize_diagram_content(current_diagram)
                    mermaid_diagrams.append('\n'.join(current_diagram))
                    self.diagram_count += 1
                    current_diagram = self.start_new_diagram(self.diagram_count)
                    self.defined_classes = set()  # Reset defined classes for new diagram
                
                # Handle class definitions
                if line.startswith(('class ', 'interface ', 'enum ', 'abstract class ')):
                    parts = line.split()
                    class_type = parts[0] if parts[0] != 'abstract' else 'abstract class'
                    class_name = self.sanitize_class_name(parts[-1] if class_type == 'class' else parts[1])
                    
                    if class_name not in self.defined_classes:
                        current_diagram.append(f"    class {class_name}")
                        self.defined_classes.add(class_name)
                        
                        if class_type in self.modifiers:
                            current_diagram.append(f"    {class_name} : {self.modifiers[class_type]}")
                    
                    current_class = class_name
                
                # Handle relationships
                elif any(re.search(pattern, line) for pattern in self.relationship_patterns):
                    for pattern, replacement in self.relationship_patterns.items():
                        if re.search(pattern, line):
                            match = re.search(pattern, line)
                            if match:
                                source = self.sanitize_class_name(match.group(1))
                                target = self.sanitize_class_name(match.group(2))
                                
                                # Ensure both classes are defined
                                if source not in self.defined_classes:
                                    current_diagram.append(f"    class {source}")
                                    self.defined_classes.add(source)
                                if target not in self.defined_classes:
                                    current_diagram.append(f"    class {target}")
                                    self.defined_classes.add(target)
                                
                                relationship = re.sub(pattern, replacement, line)
                                current_diagram.append(f"    {relationship}")
                            break
                
                # Handle methods and attributes
                elif current_class and line not in ['{', '}']:
                    line = line.strip("{ }").strip()
                    if line:
                        if '(' in line and ')' in line:
                            formatted_line = self.format_method_signature(line)
                            current_diagram.append(f"    {current_class} : {formatted_line}")
                        else:
                            formatted_line = self.format_attribute(line)
                            if formatted_line:
                                current_diagram.append(f"    {current_class} : {formatted_line}")
                
                i += 1
        
        # Add the last diagram
        if len(current_diagram) > 2:  # More than just the header
            current_diagram = self.organize_diagram_content(current_diagram)
            mermaid_diagrams.append('\n'.join(current_diagram))
        
        return mermaid_diagrams

    def organize_diagram_content(self, diagram_lines):
        """Organize diagram content to ensure proper syntax"""
        header = diagram_lines[:2]  # Keep the classDiagram and direction lines
        class_definitions = []
        class_contents = []
        relationships = []
        
        for line in diagram_lines[2:]:
            line = line.strip()
            if line.startswith('class '):
                class_definitions.append(line)
            elif ' : ' in line and not any(rel in line for rel in ['-->', '--|>', '--*', '--o', '..>']):
                class_contents.append(line)
            elif any(rel in line for rel in ['-->', '--|>', '--*', '--o', '..>']):
                relationships.append(line)
        
        # Reconstruct the diagram in the correct order
        return header + class_definitions + class_contents + relationships

def main():
    parser = argparse.ArgumentParser(description='Convert PlantUML to various diagram formats')
    parser.add_argument('input_file', help='Input PlantUML file path')
    parser.add_argument('--type', '-t', choices=['sequence', 'class', 'interactive', 'all'], 
                      default='class', help='Type of diagram (default: class)')
    parser.add_argument('--template', help='Path to HTML template file for interactive diagram',
                      default='template.html')
    
    args = parser.parse_args()


    
    # Assuming `data` is your diagram's nodes and edges
    data = {
            "nodes": [
                {"data": {"id": "class1", "label": "Class 1"}},
                {"data": {"id": "class2", "label": "Class 2"}}
                ],
                "edges": [
                {"data": {"source": "class1", "target": "class2", "label": "inherits"}}
                ]
            }

    # Serialize data as JSON for embedding in JavaScript

    escaped_data = html.escape(json.dumps(data))
    serialized_data = escaped_data

    
    try:
        print(f"Reading file: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            puml_content = f.read()
        
        base_filename = os.path.splitext(args.input_file)[0]
        
        # Process based on type
        if args.type in ['interactive', 'all']:
            # Generate interactive HTML diagram
            output_file = f"{base_filename}_interactive.html"
            
            if not os.path.exists(args.template):
                print(f"Warning: Template file {args.template} not found.")
                # Save the template content from the earlier artifact
                with open(args.template, 'w', encoding='utf-8') as f:
                    f.write(TEMPLATE_HTML)  # This should be defined elsewhere in your code
                print(f"Created template file: {args.template}")


                
            
            
            InteractiveDiagramConverter.convert_to_interactive_html(puml_content, args.template, output_file)
            print(f"Created interactive diagram: {output_file}")
            print(serialized_data)
        
        if args.type in ['class', 'sequence', 'all']:
            # Generate Mermaid diagram(s)
            converter = DiagramConverter()
            if args.type in ['class', 'all']:
                mermaid_diagrams = converter.convert_class_diagram(puml_content)
                diagram_type = 'class'
            else:
                mermaid_diagrams = [converter.convert_sequence_diagram(puml_content)]
                diagram_type = 'sequence'
            
            # Create output files for each diagram part
            for i, diagram in enumerate(mermaid_diagrams, 1):
                output_file = f"{base_filename}_part{i}.mmd" if len(mermaid_diagrams) > 1 else f"{base_filename}.mmd"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(diagram)
                print(f"Created diagram part {i}: {output_file}")
            
            print(f"\nMermaid diagram conversion completed!")
            print(f"Created {len(mermaid_diagrams)} {diagram_type} diagram{'s' if len(mermaid_diagrams) > 1 else ''}")
        
        if args.type == 'all':
            print("\nAll conversions completed successfully!")
            print("Generated both Mermaid and interactive HTML diagrams.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()