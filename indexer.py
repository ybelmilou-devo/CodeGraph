# import os
# import ast
# import sys
# import networkx as nx
# from tqdm import tqdm
# from flask import Flask, send_file, jsonify, request
# from pyvis.network import Network

# # -------------------- Indexer --------------------
# class InternalFunctionIndexer(ast.NodeVisitor):
#     def __init__(self, filepath):
#         self.filepath = filepath
#         self.defined = {}
#         self.calls = []
#         self.current = None

#     def visit_FunctionDef(self, node):
#         func_name = f"{os.path.basename(self.filepath)}:{node.name}"
#         self.defined[func_name] = (self.filepath, node.lineno, node.end_lineno)
#         prev = self.current
#         self.current = func_name
#         self.generic_visit(node)
#         self.current = prev

#     def visit_Call(self, node):
#         if not self.current:
#             return
#         if isinstance(node.func, ast.Name):
#             callee = node.func.id
#         elif isinstance(node.func, ast.Attribute):
#             callee = node.func.attr
#         else:
#             return
#         self.calls.append((self.current, callee))
#         self.generic_visit(node)

# def index_file(filepath):
#     with open(filepath, "r", encoding="utf-8") as f:
#         try:
#             tree = ast.parse(f.read())
#         except SyntaxError:
#             return {}, []
#     indexer = InternalFunctionIndexer(filepath)
#     indexer.visit(tree)
#     return indexer.defined, indexer.calls

# def index_directory(directory):
#     py_files = [
#         os.path.join(root, file)
#         for root, _, files in os.walk(directory)
#         for file in files if file.endswith(".py")
#     ]

#     all_defined = {}
#     all_calls = []

#     print(f"📦 Found {len(py_files)} Python files in {os.path.abspath(directory)}\n")

#     for path in tqdm(py_files, desc="Indexing files", ncols=80, colour="cyan"):
#         defined, calls = index_file(path)
#         all_defined.update(defined)
#         all_calls.extend(calls)

#     filtered = [
#         (caller, callee)
#         for caller, callee in all_calls
#         if any(callee == d.split(":")[1] for d in all_defined)
#     ]
#     return filtered, all_defined

# # -------------------- Graph --------------------
# def make_interactive_graph(calls, output_file="graph.html"):
#     G = nx.DiGraph()
#     G.add_edges_from(calls)

#     net = Network(
#         height="90vh",
#         width="100%",
#         directed=True,
#         bgcolor="#1e1e1e",
#         font_color="white"
#     )
#     net.from_nx(G)
#     net.force_atlas_2based()

#     # Add side panel for function code with syntax highlighting
#     net.write_html(output_file, open_browser=False)
#     inject_code_panel(output_file)
#     print(f"✅ Graph written to {output_file}")
#     return output_file

# def inject_code_panel(html_path):
#     """Injects a side panel and JS code into PyVis HTML for displaying source with syntax highlighting."""
#     with open(html_path, "r", encoding="utf-8") as f:
#         html = f.read()

#     inject_script = """
#     <!-- Highlight.js CSS & JS -->
#     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
#     <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
#     <script>hljs.highlightAll();</script>

#     <div id="code-panel"
#          style="position:fixed; top:10px; right:10px; width:45%; height:90%;
#                 background:#1e1e1e; color:#eee; overflow:auto; padding:10px;
#                 border-left:2px solid #555; font-family:monospace;
#                 display:none; z-index:9999;">
#         <h3 id="func-title" style="color:#6cf;">Function Source</h3>
#         <pre><code id="func-code" class="python"></code></pre>
#     </div>

#     <script>
#     network.on("click", function (params) {
#         if (params.nodes.length > 0) {
#             const funcName = params.nodes[0];
#             fetch(`/source?func=${encodeURIComponent(funcName)}`)
#                 .then(r => r.json())
#                 .then(data => {
#                     const codeElem = document.getElementById("func-code");
#                     document.getElementById("code-panel").style.display = "block";
#                     document.getElementById("func-title").innerText = funcName;

#                     // Use textContent to preserve formatting
#                     codeElem.textContent = data.source || "No source found";
#                     hljs.highlightElement(codeElem);
#                 });
#         }
#     });
#     </script>

#     """

#     html = html.replace("</body>", inject_script + "\n</body>")

#     with open(html_path, "w", encoding="utf-8") as f:
#         f.write(html)

# # -------------------- Flask App --------------------
# app = Flask(__name__)
# project_path = None
# function_map = {}  # Maps function name -> (filepath, start, end)

# @app.route("/")
# def serve_graph():
#     global function_map
#     calls, function_map = index_directory(project_path)
#     html_path = make_interactive_graph(calls)
#     return send_file(html_path)

# @app.route("/source")
# def get_source():
#     func = request.args.get("func")
#     if func not in function_map:
#         return jsonify({"source": "Function not found"}), 404

#     filepath, start, end = function_map[func]
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             lines = f.readlines()[start - 1:end]
#             code = "".join(lines)
#         return jsonify({"source": code})
#     except Exception as e:
#         return jsonify({"source": f"Error reading file: {e}"}), 500

# # -------------------- Main --------------------
# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("❌ Usage: python3 indexer_interactive.py <project_path>")
#         sys.exit(1)

#     project_path = sys.argv[1]
#     if not os.path.exists(project_path):
#         print(f"❌ Path not found: {project_path}")
#         sys.exit(1)

#     print(f"📁 Using project path: {os.path.abspath(project_path)}")
#     app.run(debug=True)


import os
import ast
import sys
import networkx as nx
from tqdm import tqdm
from flask import Flask, send_file, jsonify, request
from pyvis.network import Network

# -------------------- Indexer --------------------
class InternalFunctionIndexer(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.defined = {}
        self.calls = []
        self.current = None

    def visit_FunctionDef(self, node):
        func_name = f"{os.path.basename(self.filepath)}:{node.name}"
        # Use end_lineno if available (Python 3.8+)
        end_line = getattr(node, 'end_lineno', node.lineno)
        self.defined[func_name] = (self.filepath, node.lineno, end_line)
        prev = self.current
        self.current = func_name
        self.generic_visit(node)
        self.current = prev

    def visit_Call(self, node):
        if not self.current:
            return
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        else:
            return
        self.calls.append((self.current, callee))
        self.generic_visit(node)

def index_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return {}, []
    indexer = InternalFunctionIndexer(filepath)
    indexer.visit(tree)
    return indexer.defined, indexer.calls

def index_directory(directory):
    py_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files if file.endswith(".py")
    ]

    all_defined = {}
    all_calls = []

    print(f"📦 Found {len(py_files)} Python files in {os.path.abspath(directory)}\n")

    for path in tqdm(py_files, desc="Indexing files", ncols=80, colour="cyan"):
        defined, calls = index_file(path)
        all_defined.update(defined)
        all_calls.extend(calls)

    # Only keep calls where callee exists in all_defined
    filtered = [
        (caller, f"{os.path.basename(all_defined[d][0])}:{callee}")
        for caller, callee in all_calls
        for d in all_defined
        if callee == d.split(":")[1]
    ]
    return filtered, all_defined

# -------------------- Graph --------------------
def make_interactive_graph(calls, output_file="graph.html"):
    G = nx.DiGraph()
    G.add_edges_from(calls)

    net = Network(
        height="90vh",
        width="100%",
        directed=True,
        bgcolor="#1e1e1e",
        font_color="white"
    )
    net.from_nx(G)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.05, damping=0.4, overlap=0)
    net.show_buttons(filter_=['physics'])


    # Add side panel for function code with syntax highlighting
    net.write_html(output_file, open_browser=False)
    inject_code_panel(output_file)
    print(f"✅ Graph written to {output_file}")
    return output_file

def inject_code_panel(html_path):
    """Injects a side panel and JS code into PyVis HTML for displaying source with syntax highlighting."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    inject_script = """
    <!-- Highlight.js CSS & JS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>

    <div id="code-panel"
         style="position:fixed; top:10px; right:10px; width:45%; height:90%;
                background:#1e1e1e; color:#eee; overflow:auto; padding:10px;
                border-left:2px solid #555; font-family:monospace;
                display:none; z-index:9999;">
        <h3 id="func-title" style="color:#6cf;">Function Source</h3>
        <pre><code id="func-code" class="python"></code></pre>
    </div>

    <script>
    network.on("click", function (params) {
        if (params.nodes.length > 0) {
            const funcName = params.nodes[0];
            fetch(`/source?func=${encodeURIComponent(funcName)}`)
                .then(r => r.json())
                .then(data => {
                    const codeElem = document.getElementById("func-code");
                    document.getElementById("code-panel").style.display = "block";
                    document.getElementById("func-title").innerText = funcName;

                    // Use textContent to preserve formatting
                    codeElem.textContent = data.source || "No source found";
                    hljs.highlightElement(codeElem);
                });
        }
    });
    </script>
    """

    html = html.replace("</body>", inject_script + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

# -------------------- Flask App --------------------
app = Flask(__name__)
project_path = None
function_map = {}  # Maps "filename:function" -> (filepath, start, end)

@app.route("/")
def serve_graph():
    global function_map
    calls, function_map = index_directory(project_path)
    html_path = make_interactive_graph(calls)
    return send_file(html_path)

@app.route("/source")
def get_source():
    func = request.args.get("func")
    if func not in function_map:
        return jsonify({"source": "Function not found"}), 404

    filepath, start, end = function_map[func]
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()[start - 1:end]
            code = "".join(lines)
        return jsonify({"source": code})
    except Exception as e:
        return jsonify({"source": f"Error reading file: {e}"}), 500

# -------------------- Main --------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python3 indexer_interactive.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    if not os.path.exists(project_path):
        print(f"❌ Path not found: {project_path}")
        sys.exit(1)

    print(f"📁 Using project path: {os.path.abspath(project_path)}")
    app.run(debug=True)
