# Dockerfile (and other files) generator.

import argparse
import difflib
import os
import platform
import jinja2

# Define the ANSI color functions
red = lambda text: f"\033[38;2;255;0;0m{text}\033[38;2;255;255;255m"
green = lambda text: f"\033[38;2;0;255;0m{text}\033[38;2;255;255;255m"
blue = lambda text: f"\033[38;2;0;0;255m{text}\033[38;2;255;255;255m"
yellow = lambda text: f"\033[38;2;255;255;0m{text}\033[38;2;255;255;255m"

# Define the template directory
TEMPLATE_DIR = f'{os.path.dirname(__file__)}/templates'

# Define the generator class - contains all the logic for rendering the templates
class Generator:
    def __init__(self, args) -> None:
        self.args = args
        self.answer = ''

        if args.force:
            self.answer = 'a'
        elif args.skip:
            self.answer = 'N'
        
    @property
    def pythonVersion(self) -> str:
        return platform.python_version()
    
    def run(self) -> None:
        templates = {
            'Dockerfile.jinja': 'Dockerfile',          
        }

        # ... add additional templates here, possibly based on scanning the source ...

        # render each template
        for template, output in templates.items():
            self.writeTemplateFile(template, output)

    def writeTemplateFile(self, template, output) -> None:
        # read the file before the change
        try:
            with open(output) as file:
                before = file.read().splitlines()
        except FileNotFoundError:
            before = []
    
        # render the template
        with open(os.path.join(TEMPLATE_DIR, template)) as file:
            template = jinja2.Template(file.read(), trim_blocks=True, lstrip_blocks=True)
            result = template.render(dict(config=self, args=self.args)).splitlines()

        # write the file if it doesn't exist; if it has changed ask the user what to do
        if before == None:
            print(f"{green('create'.center(11))} {output}")
            with open(output, 'w') as file:
                file.write('\n'.join(result))
        elif before == result:
            print(f"{blue('identical'.center(11))} {output}")
        elif self.answer == 'N':
            print(f"{blue('skipped'.center(11))} {output}")
        else:
            if self.answer != 'a':
                print(f"{red('conflict'.center(11))} {output}")

            while True:
                if self.answer != 'a':
                    self.answer = input(f'Overwrite {output}? (enter "h" for help) [Ynaqdh] ').lower()

                if self.answer == 'y' or self.answer == '' or self.answer == 'a':
                    print(f"{yellow('forced'.center(11))} {output}")

                    with open(output, 'w') as file:
                        file.write('\n'.join(result))
                    return
                
                elif self.answer == 'n':
                    return  
                                  
                elif self.answer == 'd':
                    self.colorize_diff(output, before, result)
                
                elif self.answer == 'q':
                    exit()

                else:
                    print('  Y - yes, overwrite')
                    print('  n - no, do not overwrite')
                    print('  a - all, overwrite this and all others')
                    print('  q - quit, abort')
                    print('  d - diff, show the differences between the old and the new')
                    print('  h - help, show this help')

    # Colorize each line of the diff based on the type of change 
    def colorize_diff(self, name, file1, file2):
        for line in difflib.unified_diff(file1, file2, fromfile=f"{name} current", tofile=f"{name} proposed", lineterm=''):
            if line.startswith('---') or line.startswith('+++'):
                print(line)
            elif line.startswith('@@'):
                print(blue(line))
            elif line.startswith('+'):
                print(green(line))
            elif line.startswith('-'):
                print(red(line))
            else:
                print(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates a Dockerfile.')
    parser.add_argument('--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('--skip', action='store_true', help='Skip existing files')
    args = parser.parse_args()

    Generator(args).run()
