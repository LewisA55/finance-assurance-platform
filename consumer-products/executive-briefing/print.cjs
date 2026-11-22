const {existsSync} = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require("../../web/node_modules/playwright");

const defaultInput = path.join(__dirname, "exports/output/pdf/Nexus-June-2026-Executive-Deck.html");
const input = path.resolve(process.argv[2] || defaultInput);
const output = input.replace(/\.html$/i, ".pdf");

async function printDeck() {
    if (!existsSync(input) || output === input) {
        throw new Error("Provide an existing generated .html file.");
    }
    const executablePath = process.env.NEXUS_PRINT_BROWSER;
    const browser = await chromium.launch({headless: true, executablePath});
    try {
        const page = await browser.newPage({viewport: {width: 1280, height: 720}});
        await page.goto(pathToFileURL(input).href, {waitUntil: "load"});
        await page.emulateMedia({media: "print"});
        await page.evaluate(() => document.fonts.ready);

        // Every slide must be exactly 16:9, and nothing may spill past its
        // footer or its edges: a clipped figure is worse than a failed build.
        const layout = await page.evaluate(() => {
            const slides = [...document.querySelectorAll(".slide")];
            const problems = [];
            slides.forEach((slide, index) => {
                const box = slide.getBoundingClientRect();
                if (Math.abs(box.width - 1280) > 0.5 || Math.abs(box.height - 720) > 0.5
                    || slide.scrollHeight > slide.clientHeight + 1 || slide.scrollWidth > slide.clientWidth + 1) {
                    problems.push(`slide ${index + 1} size or overflow`);
                }
                const foot = slide.querySelector(".slide-foot");
                const limit = foot ? foot.getBoundingClientRect().top : box.bottom;
                for (const element of slide.querySelectorAll("*")) {
                    if (foot && (element === foot || foot.contains(element))) continue;
                    const rect = element.getBoundingClientRect();
                    if (rect.height && (rect.bottom > limit + 0.5 || rect.right > box.right + 0.5)) {
                        problems.push(`slide ${index + 1}: ${element.tagName.toLowerCase()}.${element.className.baseVal ?? element.className}`);
                        break;
                    }
                }
            });
            const links = [...document.querySelectorAll("a[href^='#']")];
            return {
                slides: slides.length,
                expected: Number(document.body.dataset.slides),
                problems,
                brokenLinks: links.filter(link => !document.getElementById(link.hash.slice(1))).length,
            };
        });
        if (layout.slides !== layout.expected || layout.problems.length || layout.brokenLinks) {
            throw new Error("Deck layout or evidence links differ: " + JSON.stringify(layout));
        }
        await page.pdf({path: output, printBackground: true, preferCSSPageSize: true, tagged: true, outline: true});
    } finally {
        await browser.close();
    }
    process.stdout.write(output + "\n");
}

printDeck().catch(error => {
    process.stderr.write(error.message + "\n");
    process.exitCode = 1;
});
