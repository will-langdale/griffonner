# AI instructions

Copy and paste this into any LLM to get help with Griffonner:

```
I'm using Griffonner, a Python documentation generator. Here's how it works:

1. Griffonner uses Griffe to parse Python modules and Jinja2 templates to generate documentation
2. I create markdown files with YAML frontmatter that specify:
   - template: path to Jinja2 template (e.g., "python/simple/module.md.jinja2")  
   - output: list of outputs with filename and griffe_target (Python module name)
   - custom_vars: any custom variables for the template

3. Templates get access to:
   - obj: the raw Griffe object with all module/class/function data
   - custom_vars: any variables I defined in frontmatter
   - source_content: the markdown content after frontmatter
   - source_path: path to the source file

4. Common Griffe object properties:
   - obj.name: module/class/function name
   - obj.kind.value: "module", "class", "function", etc.
   - obj.docstring.summary: first line of docstring  
   - obj.docstring.description: full docstring text
   - obj.members: dictionary of child objects
   - obj.signature: function signature info
   - obj.signature.parameters: list of parameters
   - obj.signature.returns: return type annotation

5. CLI usage:
   - griffonner generate docs/pages/ --output docs/output
   - griffonner templates --template-dir docs/templates

Please help me create templates or frontmatter for documenting my Python code.
```