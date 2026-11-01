/**
 * termynal.js
 * A lightweight, modern and extensible animated terminal window widget.
 *
 * @author Ines Montani <ines@ines.io> & Sebastián Ramírez <tiangolo@gmail.com>
 * @license MIT
 */

'use strict';

class Termynal {
    constructor(container = '#termynal', options = {}) {
        this.container = (typeof container === 'string') ? document.querySelector(container) : container;
        this.pfx = `data-${options.prefix || 'ty'}`;
        this.originalStartDelay = this.startDelay = options.startDelay
            || parseFloat(this.container.getAttribute(`${this.pfx}-startDelay`)) || 600;
        this.originalTypeDelay = this.typeDelay = options.typeDelay
            || parseFloat(this.container.getAttribute(`${this.pfx}-typeDelay`)) || 80;
        this.originalLineDelay = this.lineDelay = options.lineDelay
            || parseFloat(this.container.getAttribute(`${this.pfx}-lineDelay`)) || 1200;
        this.progressLength = options.progressLength
            || parseFloat(this.container.getAttribute(`${this.pfx}-progressLength`)) || 40;
        this.progressChar = options.progressChar
            || this.container.getAttribute(`${this.pfx}-progressChar`) || '█';
        this.progressPercent = options.progressPercent
            || parseFloat(this.container.getAttribute(`${this.pfx}-progressPercent`)) || 100;
        this.cursor = options.cursor
            || this.container.getAttribute(`${this.pfx}-cursor`) || '▋';
        this.lineData = this.lineDataToElements(options.lineData || []);
        this.loadLines();
        if (!options.noInit) this.init();
    }

    loadLines() {
        const finish = this.generateFinish();
        finish.style.visibility = 'hidden';
        this.container.appendChild(finish);
        this.lines = [...this.container.querySelectorAll(`[${this.pfx}]`)].concat(this.lineData);
        for (let line of this.lines) {
            line.style.visibility = 'hidden';
            this.container.appendChild(line);
        }
        const restart = this.generateRestart();
        restart.style.visibility = 'hidden';
        this.container.appendChild(restart);
        this.container.setAttribute('data-termynal', '');
    }

    init() {
        const containerStyle = getComputedStyle(this.container);
        this.container.style.width = containerStyle.width !== '0px' ? containerStyle.width : undefined;
        this.container.style.minHeight = containerStyle.height !== '0px' ? containerStyle.height : undefined;

        this.container.setAttribute('data-termynal', '');
        this.container.innerHTML = '';
        for (let line of this.lines) {
            line.style.visibility = 'visible';
        }
        this.start();
    }

    async start() {
        this.addFinish();
        await this._wait(this.startDelay);

        for (let line of this.lines) {
            const type = line.getAttribute(this.pfx);
            const delay = line.getAttribute(`${this.pfx}-delay`) || this.lineDelay;

            if (type === 'input') {
                line.setAttribute(`${this.pfx}-cursor`, this.cursor);
                await this.type(line);
                await this._wait(delay);
            } else if (type === 'progress') {
                await this.progress(line);
                await this._wait(delay);
            } else {
                this.container.appendChild(line);
                await this._wait(delay);
            }

            line.removeAttribute(`${this.pfx}-cursor`);
        }
        this.addRestart();
        if (this.finishElement) {
            this.finishElement.style.visibility = 'hidden';
        }
        this.lineDelay = this.originalLineDelay;
        this.typeDelay = this.originalTypeDelay;
        this.startDelay = this.originalStartDelay;
    }

    generateRestart() {
        const restart = document.createElement('button');
        restart.type = 'button';
        restart.onclick = () => {
            this.container.innerHTML = '';
            this.init();
        };
        restart.setAttribute('data-terminal-control', '');
        restart.innerHTML = 'restart ↻';
        return restart;
    }

    generateFinish() {
        const finish = document.createElement('button');
        finish.type = 'button';
        finish.onclick = () => {
            this.lineDelay = 0;
            this.typeDelay = 0;
            this.startDelay = 0;
        };
        finish.setAttribute('data-terminal-control', '');
        finish.innerHTML = 'fast →';
        this.finishElement = finish;
        return finish;
    }

    addRestart() {
        const restart = this.generateRestart();
        this.container.appendChild(restart);
    }

    addFinish() {
        const finish = this.generateFinish();
        this.container.appendChild(finish);
    }

    async type(line) {
        const chars = [...line.textContent];
        line.textContent = '';
        this.container.appendChild(line);

        for (let char of chars) {
            const delay = line.getAttribute(`${this.pfx}-typeDelay`) || this.typeDelay;
            await this._wait(delay);
            line.textContent += char;
        }
    }

    async progress(line) {
        const progressLength = line.getAttribute(`${this.pfx}-progressLength`) || this.progressLength;
        const progressChar = line.getAttribute(`${this.pfx}-progressChar`) || this.progressChar;
        const chars = progressChar.repeat(progressLength);
        const progressPercent = line.getAttribute(`${this.pfx}-progressPercent`) || this.progressPercent;
        line.textContent = '';
        this.container.appendChild(line);

        for (let i = 1; i < chars.length + 1; i++) {
            await this._wait(this.typeDelay);
            const percent = Math.round((i / chars.length) * 100);
            line.textContent = `${chars.slice(0, i)} ${percent}%`;
            if (percent > progressPercent) break;
        }
    }

    _wait(time) {
        return new Promise(resolve => setTimeout(resolve, time));
    }

    lineDataToElements(lineData) {
        return lineData.map(line => {
            let div = document.createElement('div');
            div.innerHTML = `<span ${this._attributes(line)}>${line.value || ''}</span>`;
            return div.firstElementChild;
        });
    }

    _attributes(line) {
        let attrs = '';
        for (let prop in line) {
            if (prop === 'class') {
                attrs += ` class="${line[prop]}" `;
                continue;
            }
            if (prop === 'type') {
                attrs += `${this.pfx}="${line[prop]}" `;
            } else if (prop !== 'value') {
                attrs += `${this.pfx}-${prop}="${line[prop]}" `;
            }
        }
        return attrs;
    }
}

function escapePlainCliLine(line) {
    return line
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function prepareTermynalLines(lines, isRichHtml) {
    if (isRichHtml) {
        return lines.join('<br>');
    }
    return lines.map(escapePlainCliLine).join('<br>');
}

function setupTermynal() {
    document.querySelectorAll('.use-termynal').forEach(node => {
        if (node.dataset.termynalProcessed) return;
        node.dataset.termynalProcessed = 'true';
        node.style.display = 'block';
        new Termynal(node, { lineDelay: 500 });
    });

    const progressLiteralStart = '---> 100%';
    const promptLiteralStart = '$ ';
    const customPromptLiteralStart = '# ';
    const termynalActivateClass = 'termy';
    let termynals = [];

    function createTermynals() {
        document
            .querySelectorAll(`.${termynalActivateClass} .highlight code, .${termynalActivateClass} pre code`)
            .forEach(node => {
                if (node.dataset.termynalProcessed) return;
                node.dataset.termynalProcessed = 'true';

                const text = node.textContent;
                const lines = text.split('\n');
                const hasHtmlAttribute = /<[A-Za-z][^>]*=/.test(text);
                const hasClosingTag = /<\/[a-zA-Z0-9]/.test(text);
                const isRichHtml = hasHtmlAttribute || hasClosingTag;
                const useLines = [];
                let buffer = [];

                function saveBuffer() {
                    if (buffer.length) {
                        let isBlankSpace = true;
                        buffer.forEach(line => {
                            if (line.trim()) isBlankSpace = false;
                        });
                        const dataValue = {};
                        if (isBlankSpace) {
                            dataValue['delay'] = 0;
                        }
                        if (buffer[buffer.length - 1] === '') {
                            buffer.push('');
                        }
                        dataValue['value'] = prepareTermynalLines(buffer, isRichHtml);
                        useLines.push(dataValue);
                        buffer = [];
                    }
                }

                for (let line of lines) {
                    if (line === progressLiteralStart) {
                        saveBuffer();
                        useLines.push({ type: 'progress' });
                    } else if (line.startsWith(promptLiteralStart)) {
                        saveBuffer();
                        const value = line.replace(promptLiteralStart, '').trimEnd();
                        useLines.push({ type: 'input', value: value });
                    } else if (line.startsWith('// ')) {
                        saveBuffer();
                        let comment = line.replace('// ', '').trimEnd();
                        if (!isRichHtml) {
                            comment = escapePlainCliLine(comment);
                        }
                        useLines.push({
                            value: '💬 ' + comment,
                            class: 'termynal-comment',
                            delay: 0,
                        });
                    } else if (line.startsWith(customPromptLiteralStart)) {
                        saveBuffer();
                        const promptStart = line.indexOf(promptLiteralStart);
                        const prompt = promptStart !== -1
                            ? line.slice(0, promptStart).replace(customPromptLiteralStart, '')
                            : '>';
                        const value = promptStart !== -1
                            ? line.slice(promptStart + promptLiteralStart.length)
                            : line.replace(customPromptLiteralStart, '');
                        useLines.push({
                            type: 'input',
                            value: value,
                            prompt: prompt,
                        });
                    } else {
                        buffer.push(line);
                    }
                }
                saveBuffer();

                const inputCommands = useLines.filter(line => line.type === 'input').map(line => line.value).join('\n');
                node.textContent = inputCommands;
                const div = document.createElement('div');
                node.style.display = 'none';
                node.after(div);
                const termynal = new Termynal(div, {
                    lineData: useLines,
                    noInit: true,
                    lineDelay: 500,
                });
                termynals.push(termynal);
            });
    }

    function loadVisibleTermynals() {
        termynals = termynals.filter(termynal => {
            if (termynal.container.getBoundingClientRect().top - window.innerHeight <= 0) {
                termynal.init();
                return false;
            }
            return true;
        });
    }

    window.addEventListener('scroll', loadVisibleTermynals);
    createTermynals();
    loadVisibleTermynals();
}

if (typeof document$ !== 'undefined') {
    document$.subscribe(() => {
        setupTermynal();
    });
} else {
    document.addEventListener('DOMContentLoaded', () => {
        setupTermynal();
    });
}
