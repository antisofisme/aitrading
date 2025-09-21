import mermaid from 'mermaid';
import puppeteer from 'puppeteer';
import { JSDOM } from 'jsdom';
import { PDFDocument } from 'pdf-lib';
import { OutputFormat } from '../core/types';

export class OutputFormatter {
  private browser: puppeteer.Browser | null = null;

  /**
   * Convert Mermaid code to specified output format
   */
  async convert(mermaidCode: string, format: OutputFormat): Promise<string | Buffer> {
    switch (format) {
      case 'svg':
        return await this.generateSVG(mermaidCode);
      case 'png':
        return await this.generatePNG(mermaidCode);
      case 'pdf':
        return await this.generatePDF(mermaidCode);
      case 'html':
        return await this.generateHTML(mermaidCode);
      case 'json':
        return this.generateJSON(mermaidCode);
      default:
        throw new Error(`Unsupported output format: ${format}`);
    }
  }

  /**
   * Generate SVG output using Mermaid
   */
  private async generateSVG(mermaidCode: string): Promise<string> {
    try {
      // Use JSDOM for server-side rendering
      const dom = new JSDOM('<!DOCTYPE html><html><body><div id="mermaid"></div></body></html>');
      global.window = dom.window as any;
      global.document = dom.window.document;

      // Initialize Mermaid
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose'
      });

      // Generate SVG
      const element = document.getElementById('mermaid')!;
      const { svg } = await mermaid.render('diagram', mermaidCode, element);

      // Clean up
      delete (global as any).window;
      delete (global as any).document;

      return svg;
    } catch (error) {
      console.error('SVG generation failed:', error);
      throw new Error(`SVG generation failed: ${error.message}`);
    }
  }

  /**
   * Generate PNG output using Puppeteer
   */
  private async generatePNG(mermaidCode: string): Promise<Buffer> {
    try {
      const browser = await this.getBrowser();
      const page = await browser.newPage();

      // Set viewport for consistent rendering
      await page.setViewport({ width: 1200, height: 800 });

      // Create HTML content with Mermaid
      const html = this.createMermaidHTML(mermaidCode);
      await page.setContent(html);

      // Wait for Mermaid to render
      await page.waitForSelector('#mermaid svg', { timeout: 10000 });

      // Get the SVG element dimensions
      const svgElement = await page.$('#mermaid svg');
      if (!svgElement) {
        throw new Error('SVG element not found');
      }

      // Take screenshot of the SVG
      const screenshot = await svgElement.screenshot({
        type: 'png',
        omitBackground: true
      });

      await page.close();
      return screenshot;
    } catch (error) {
      console.error('PNG generation failed:', error);
      throw new Error(`PNG generation failed: ${error.message}`);
    }
  }

  /**
   * Generate PDF output
   */
  private async generatePDF(mermaidCode: string): Promise<Buffer> {
    try {
      // First generate PNG
      const pngBuffer = await this.generatePNG(mermaidCode);

      // Create PDF with the PNG
      const pdfDoc = await PDFDocument.create();
      const page = pdfDoc.addPage();

      // Embed the PNG image
      const pngImage = await pdfDoc.embedPng(pngBuffer);
      const pngDims = pngImage.scale(0.75); // Scale down if needed

      // Draw the image on the page
      page.drawImage(pngImage, {
        x: 50,
        y: page.getHeight() - pngDims.height - 50,
        width: pngDims.width,
        height: pngDims.height,
      });

      return Buffer.from(await pdfDoc.save());
    } catch (error) {
      console.error('PDF generation failed:', error);
      throw new Error(`PDF generation failed: ${error.message}`);
    }
  }

  /**
   * Generate interactive HTML output
   */
  private async generateHTML(mermaidCode: string): Promise<string> {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 100%;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .diagram-container {
            text-align: center;
            margin: 20px 0;
        }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .controls button {
            margin: 0 5px;
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
        }
        .controls button:hover {
            background: #f0f0f0;
        }
        .diagram-info {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
            color: #666;
        }
        #mermaid {
            min-height: 400px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Interactive Diagram</h1>

        <div class="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="toggleTheme()">Toggle Theme</button>
            <button onclick="exportSVG()">Export SVG</button>
        </div>

        <div class="diagram-container">
            <div id="mermaid">${mermaidCode}</div>
        </div>

        <div class="diagram-info">
            <strong>Instructions:</strong>
            <ul>
                <li>Use the controls above to zoom and change themes</li>
                <li>Click on diagram elements to interact (if supported)</li>
                <li>Export to SVG for use in other applications</li>
            </ul>
        </div>
    </div>

    <script>
        let currentZoom = 1;
        let isDarkTheme = false;

        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        });

        function zoomIn() {
            currentZoom *= 1.2;
            applyZoom();
        }

        function zoomOut() {
            currentZoom /= 1.2;
            applyZoom();
        }

        function resetZoom() {
            currentZoom = 1;
            applyZoom();
        }

        function applyZoom() {
            const diagram = document.querySelector('#mermaid svg');
            if (diagram) {
                diagram.style.transform = \`scale(\${currentZoom})\`;
            }
        }

        function toggleTheme() {
            isDarkTheme = !isDarkTheme;
            mermaid.initialize({
                startOnLoad: false,
                theme: isDarkTheme ? 'dark' : 'default',
                securityLevel: 'loose'
            });

            // Re-render the diagram
            const element = document.getElementById('mermaid');
            element.innerHTML = \`${mermaidCode}\`;
            mermaid.init();
        }

        function exportSVG() {
            const svg = document.querySelector('#mermaid svg');
            if (svg) {
                const svgData = new XMLSerializer().serializeToString(svg);
                const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
                const svgUrl = URL.createObjectURL(svgBlob);

                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;
                downloadLink.download = 'diagram.svg';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                URL.revokeObjectURL(svgUrl);
            }
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '=':
                    case '+':
                        e.preventDefault();
                        zoomIn();
                        break;
                    case '-':
                        e.preventDefault();
                        zoomOut();
                        break;
                    case '0':
                        e.preventDefault();
                        resetZoom();
                        break;
                }
            }
        });
    </script>
</body>
</html>`;

    return html;
  }

  /**
   * Generate JSON representation
   */
  private generateJSON(mermaidCode: string): string {
    const diagram = {
      format: 'mermaid',
      version: '1.0',
      source: mermaidCode,
      metadata: {
        generatedAt: new Date().toISOString(),
        type: this.detectDiagramType(mermaidCode),
        lineCount: mermaidCode.split('\n').length
      }
    };

    return JSON.stringify(diagram, null, 2);
  }

  /**
   * Create HTML template for Mermaid rendering
   */
  private createMermaidHTML(mermaidCode: string): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: sans-serif; }
        #mermaid { text-align: center; }
    </style>
</head>
<body>
    <div id="mermaid">${mermaidCode}</div>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        });
    </script>
</body>
</html>`;
  }

  /**
   * Detect diagram type from Mermaid code
   */
  private detectDiagramType(mermaidCode: string): string {
    const firstLine = mermaidCode.trim().split('\n')[0].toLowerCase();

    if (firstLine.includes('graph')) return 'flowchart';
    if (firstLine.includes('sequencediagram')) return 'sequence';
    if (firstLine.includes('erdiagram')) return 'er';
    if (firstLine.includes('journey')) return 'journey';
    if (firstLine.includes('gantt')) return 'gantt';
    if (firstLine.includes('pie')) return 'pie';
    if (firstLine.includes('gitgraph')) return 'gitgraph';

    return 'unknown';
  }

  /**
   * Get or create Puppeteer browser instance
   */
  private async getBrowser(): Promise<puppeteer.Browser> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
    }
    return this.browser;
  }

  /**
   * Cleanup resources
   */
  async dispose(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Batch convert multiple diagrams
   */
  async convertBatch(
    diagrams: Array<{ code: string; format: OutputFormat; id: string }>
  ): Promise<Array<{ id: string; result: string | Buffer; error?: string }>> {
    const results = await Promise.allSettled(
      diagrams.map(async diagram => ({
        id: diagram.id,
        result: await this.convert(diagram.code, diagram.format)
      }))
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          id: diagrams[index].id,
          result: '',
          error: result.reason?.message || 'Conversion failed'
        };
      }
    });
  }
}