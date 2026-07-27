"""Redirects generator module for the static-site build system.

This module scans the project, detects SOP files, validates them,
identifies duplicates and malformed files, and generates a Netlify `_redirects` file.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

from build_system.modules.base import BaseModule
from build_system.utils.fs import scan_files, normalize_name

HTML_404_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Page Not Found - 404 Error</title>
    <link rel="stylesheet" href="home_style.css">
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
</head>

<body>
    <!-- Theme Toggle -->
    <button class="theme-switch" aria-label="Toggle dark mode">
        <i data-lucide="moon" id="theme-icon"></i>
    </button>

    <header>
        <h1>Page Not Found</h1>
        <p>Maharashtra State Board Educational Resources</p>
    </header>

    <nav>
        <div class="nav-container">
            <a href="Index.html" class="nav-link"><i data-lucide="home"></i> Home</a>
            <div class="dropdown">
                <button class="dropdown-btn"><i data-lucide="book-open"></i> Commerce Stream <i
                        data-lucide="chevron-down" class="chevron"></i></button>
                <div class="dropdown-content">
                    <a href="Index.html#commerce">Advanced Web Designing</a>
                    <a href="Index.html#commerce">Digital Marketing</a>
                    <a href="Index.html#commerce">Computerised Accounting</a>
                    <a href="Index.html#commerce">Database Concepts</a>
                </div>
            </div>
            <div class="dropdown">
                <button class="dropdown-btn"><i data-lucide="microscope"></i> Science Stream <i
                        data-lucide="chevron-down" class="chevron"></i></button>
                <div class="dropdown-content">
                    <a href="Index.html#science">Advanced Web Designing</a>
                    <a href="Index.html#science">JavaScript</a>
                    <a href="Index.html#science">PHP</a>
                </div>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="card" style="text-align: center; padding: 4rem 2rem; max-width: 800px; margin: 0 auto;">
            <div style="display: flex; justify-content: center; margin-bottom: 2rem; color: var(--primary);">
                <i data-lucide="alert-triangle" style="width: 80px; height: 80px;"></i>
            </div>
            <h2 id="error-title" style="font-size: 2.2rem; margin-bottom: 1.5rem; color: var(--text-main);">Oops! Page Not Found</h2>
            <p style="font-size: 1.2rem; color: var(--text-muted); margin-bottom: 2.2rem;">
                The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
            </p>
            <a href="Index.html" class="nav-link" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; background: var(--primary); color: white; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: var(--transition);">
                <i data-lucide="arrow-left"></i> Return Home
            </a>
        </div>
    </div>

    <footer>
        <p>&copy; 2025 Std 12th IT SOPs | Maharashtra State Board Educational Resources</p>
    </footer>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        // Theme Toggle Logic
        const themeToggle = document.querySelector('.theme-switch');
        const themeIcon = document.getElementById('theme-icon');

        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            if (savedTheme === 'light') {
                themeIcon.setAttribute('data-lucide', 'sun');
            }
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }

        themeToggle.addEventListener('click', () => {
            let theme = document.documentElement.getAttribute('data-theme');
            if (theme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                themeIcon.setAttribute('data-lucide', 'sun');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                themeIcon.setAttribute('data-lucide', 'moon');
            }
            lucide.createIcons();
        });

        // Dropdown Logic
        function positionDropdown(button) {
            const dropdown = button.parentElement;
            const content = dropdown.querySelector(".dropdown-content");
            const rect = button.getBoundingClientRect();
            const contentWidth = 260;
            const gap = 6;

            content.style.visibility = 'hidden';
            content.style.opacity = '0';
            content.style.display = 'block';
            const contentHeight = content.offsetHeight;
            content.style.display = '';
            content.style.visibility = '';
            content.style.opacity = '';

            let left = rect.left + rect.width / 2 - contentWidth / 2;
            if (left < 8) left = 8;
            if (left + contentWidth > window.innerWidth - 8) left = window.innerWidth - contentWidth - 8;
            content.style.left = left + "px";

            const spaceBelow = window.innerHeight - rect.bottom;
            const spaceAbove = rect.top;
            if (spaceBelow >= contentHeight + gap || spaceBelow >= spaceAbove) {
                content.style.top = (rect.bottom + gap) + "px";
                content.style.bottom = 'auto';
                content.style.transformOrigin = 'top center';
            } else {
                content.style.top = 'auto';
                content.style.bottom = (window.innerHeight - rect.top + gap) + "px";
                content.style.transformOrigin = 'bottom center';
            }
        }

        document.querySelectorAll(".dropdown-btn").forEach((button) => {
            button.addEventListener("click", (e) => {
                e.stopPropagation();
                const dropdown = button.parentElement;
                const isActive = dropdown.classList.contains("active");

                document.querySelectorAll(".dropdown").forEach((d) => d.classList.remove("active"));
                if (!isActive) {
                    dropdown.classList.add("active");
                    positionDropdown(button);
                }
            });
        });

        document.addEventListener("click", () => {
            document.querySelectorAll(".dropdown").forEach((d) => d.classList.remove("active"));
        });

        window.addEventListener('resize', () => {
            document.querySelectorAll(".dropdown.active .dropdown-btn").forEach(button => {
                positionDropdown(button);
            });
        });
        window.addEventListener('scroll', () => {
            document.querySelectorAll(".dropdown.active .dropdown-btn").forEach(button => {
                positionDropdown(button);
            });
        }, { passive: true });
    </script>
</body>

</html>
"""



class RedirectsGenerator(BaseModule):
    """Generates a Netlify _redirects file with short URLs and validates SOP structure."""

    # Pattern for matching standard SOP files: stream_subject_sop<number>.html
    SOP_PATTERN = re.compile(
        r"^([a-zA-Z0-9\-]+)_([a-zA-Z0-9\-]+)_sop(\d+)\.html$", re.IGNORECASE
    )

    # Indicator pattern to detect if a file was intended to be an SOP file
    SOP_INDICATOR = re.compile(r"_sop", re.IGNORECASE)

    def run(self) -> bool:
        """Executes the redirect generation and validation.

        Returns:
            bool: True if completed successfully, False otherwise.
        """
        # Ensure 404.html page exists. If not, generate it.
        html_404_file = self.project_root / "404.html"
        if not html_404_file.exists():
            print("404.html not found. Creating a default theme-matching 404 page...")
            try:
                html_404_file.write_text(HTML_404_TEMPLATE, encoding="utf-8", newline="\n")
            except OSError as e:
                print(f"Error creating 404.html: {e}", file=sys.stderr)

        print("Scanning project for SOP files...")
        
        ignored_dirs = self.config.get("IGNORED_DIRS", set())
        ignored_files = self.config.get("IGNORED_FILES", set())
        subject_aliases = self.config.get("SUBJECT_ALIASES", {})

        all_files = scan_files(self.project_root, ignored_dirs)

        # Metrics trackers
        streams_found: Set[str] = set()
        subjects_found: Set[str] = set()
        sop_files_processed: List[Dict[str, Any]] = []

        invalid_filenames: List[Tuple[Path, str]] = []
        skipped_files_count = 0

        for file_path in all_files:
            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                # If for some reason the file is not relative to the project root, skip it
                skipped_files_count += 1
                continue

            parts = rel_path.parts
            filename = rel_path.name
            filename_lower = filename.lower()

            # 1. Skip explicitly ignored files
            if filename_lower in {f.lower() for f in ignored_files}:
                skipped_files_count += 1
                continue

            # 2. Skip non-HTML files
            if file_path.suffix.lower() != ".html":
                skipped_files_count += 1
                continue

            # 3. Check folder structure depth. SOP files must reside in Stream/Subject/
            if len(parts) != 3:
                # It is an HTML file but not at the expected Stream/Subject/ depth.
                # If it looks like an SOP file (contains '_sop'), it is an invalid filename.
                # Otherwise, it's just a skipped file.
                if self.SOP_INDICATOR.search(filename):
                    invalid_filenames.append(
                        (
                            rel_path,
                            f"HTML file is at incorrect directory depth {len(parts)-1} (expected 2: Stream/Subject)",
                        )
                    )
                else:
                    skipped_files_count += 1
                continue

            stream_folder = parts[0]
            subject_folder = parts[1]

            # Normalize directory names for URL comparison
            stream_code = normalize_name(stream_folder)
            subject_norm = normalize_name(subject_folder)
            expected_subject_code = subject_aliases.get(subject_norm, subject_norm)

            # Match SOP pattern
            match = self.SOP_PATTERN.match(filename)
            if match:
                file_stream = match.group(1).lower()
                file_subject = match.group(2).lower()
                sop_num_str = match.group(3)
                sop_number = int(sop_num_str)

                # Validate folder hierarchy vs filename codes
                mismatch_reasons = []
                if file_stream != stream_code:
                    mismatch_reasons.append(
                        f"stream code in filename '{file_stream}' does not match folder '{stream_code}'"
                    )
                if file_subject != expected_subject_code:
                    mismatch_reasons.append(
                        f"subject code in filename '{file_subject}' does not match expected folder code '{expected_subject_code}'"
                    )

                if mismatch_reasons:
                    reason_msg = "Mismatch: " + " and ".join(mismatch_reasons)
                    invalid_filenames.append((rel_path, reason_msg))
                else:
                    # Valid SOP file
                    streams_found.add(stream_folder)
                    subjects_found.add(f"{stream_folder}/{subject_folder}")
                    
                    short_url = f"/{stream_code}/{expected_subject_code}/sop{sop_number}"
                    
                    # Target URL must use forward slashes and match exact disk folder casing
                    dest_path = f"/{stream_folder}/{subject_folder}/{filename}".replace("\\", "/")

                    sop_files_processed.append(
                        {
                            "file_path": rel_path,
                            "short_url": short_url,
                            "destination_path": dest_path,
                            "stream": stream_folder,
                            "subject": subject_folder,
                            "subject_code": expected_subject_code,
                            "sop_number": sop_number,
                        }
                    )
            else:
                # Does not match SOP pattern.
                # If it looks like an SOP filename (contains '_sop'), classify as invalid.
                if self.SOP_INDICATOR.search(filename):
                    invalid_filenames.append(
                        (
                            rel_path,
                            "Filename contains '_sop' but does not match standard pattern 'stream_subject_sop<number>.html'",
                        )
                    )
                else:
                    skipped_files_count += 1

        # Validation: check for duplicates
        duplicate_url_groups = defaultdict(list)
        duplicate_dest_groups = defaultdict(list)
        duplicate_sop_groups = defaultdict(list)

        for sop in sop_files_processed:
            duplicate_url_groups[sop["short_url"]].append(sop["file_path"])
            duplicate_dest_groups[sop["destination_path"]].append(sop["file_path"])
            # Track duplicates of the same SOP number within the same subject code
            sop_key = (sop["stream"].lower(), sop["subject_code"], sop["sop_number"])
            duplicate_sop_groups[sop_key].append(sop["file_path"])

        # Filter duplicates
        dup_urls = {url: paths for url, paths in duplicate_url_groups.items() if len(paths) > 1}
        dup_dests = {dest: paths for dest, paths in duplicate_dest_groups.items() if len(paths) > 1}
        dup_sops = {key: paths for key, paths in duplicate_sop_groups.items() if len(paths) > 1}

        # Print warning reports for problems
        has_problems = False

        if invalid_filenames:
            has_problems = True
            print("\n--- INVALID FILENAMES ---", file=sys.stderr)
            for path, reason in invalid_filenames:
                print(f"  File: {path}\n    Reason: {reason}", file=sys.stderr)

        if dup_urls:
            has_problems = True
            print("\n--- DUPLICATE SHORT URLS ---", file=sys.stderr)
            for url, paths in dup_urls.items():
                print(f"  Short URL: {url} points to multiple files:", file=sys.stderr)
                for p in paths:
                    print(f"    - {p}", file=sys.stderr)

        if dup_dests:
            has_problems = True
            print("\n--- DUPLICATE DESTINATIONS ---", file=sys.stderr)
            for dest, paths in dup_dests.items():
                print(f"  Destination path: {dest} requested by multiple files:", file=sys.stderr)
                for p in paths:
                    print(f"    - {p}", file=sys.stderr)

        if dup_sops:
            has_problems = True
            print("\n--- DUPLICATE SOP NUMBERS WITHIN SUBJECT ---", file=sys.stderr)
            for (stream, subject, num), paths in dup_sops.items():
                print(f"  Subject '{stream}/{subject}' has duplicate SOP number '{num}' in files:", file=sys.stderr)
                for p in paths:
                    print(f"    - {p}", file=sys.stderr)

        if has_problems:
            print("\nValidation warnings reported above.\n")

        # ---------------------------------------------------------------
        # Generate redirect rules
        # ---------------------------------------------------------------
        # Sort by destination path for 301s, by short URL for 200s
        sorted_by_dest  = sorted(sop_files_processed, key=lambda s: s["destination_path"])
        sorted_by_short = sorted(sop_files_processed, key=lambda s: s["short_url"])

        rules_301: List[str] = []
        rules_200: List[str] = []
        written_dests: Set[str] = set()
        written_urls:  Set[str] = set()

        # --- 301 rules: old HTML path → clean short URL ---
        rules_301_data = []
        for sop in sorted_by_dest:
            dest  = sop["destination_path"]
            url   = sop["short_url"]
            
            # Form variations
            variations = [dest]
            if dest.endswith(".html"):
                variations.append(dest[:-5])
            
            # Add lowercase versions to support case-sensitive matching
            all_variations = []
            for v in variations:
                all_variations.append(v)
                all_variations.append(v.lower())
                
            for v in all_variations:
                if v not in written_dests:
                    written_dests.add(v)
                    rules_301_data.append((v, url))

        # Sort all 301 rules alphabetically by source path
        rules_301_data_sorted = sorted(rules_301_data, key=lambda x: x[0])
        for src, target in rules_301_data_sorted:
            rules_301.append(f"{src:<64}    {target:<24}    301!")

        # --- 200 rules: clean short URL → actual HTML file ---
        for sop in sorted_by_short:
            url  = sop["short_url"]
            dest = sop["destination_path"]
            if url in written_urls:
                continue
            written_urls.add(url)
            rules_200.append(f"{url:<24}    {dest:<64}    200")

        # --- Static rules: coming-soon + wildcard 404 (always last) ---
        static_rules: List[str] = [
            f"{'/coming-soon':<24}    {'/coming_soon.html':<64}    200",
            f"{'/*':<24}    {'/404.html':<64}    404",
        ]

        # Combine: 301s, then 200s, then static rules
        all_rules = rules_301 + rules_200 + static_rules

        # Write to file
        redirects_file = self.project_root / "_redirects"
        try:
            with open(redirects_file, "w", encoding="utf-8", newline="\n") as f:
                # Section headers as comments
                if rules_301:
                    f.write("# 301 redirects — canonical long URL → clean short URL\n")
                    f.write("\n".join(rules_301))
                    f.write("\n\n")
                if rules_200:
                    f.write("# 200 rewrites — clean short URL → actual HTML file\n")
                    f.write("\n".join(rules_200))
                    f.write("\n\n")
                f.write("# Static rules\n")
                f.write("\n".join(static_rules))
                f.write("\n")
        except OSError as e:
            print(f"Error writing to _redirects file: {e}", file=sys.stderr)
            return False

        # ---------------------------------------------------------------
        # Console summary
        # ---------------------------------------------------------------
        total_rules = len(rules_301) + len(rules_200) + len(static_rules)

        print(f"Streams found:         {len(streams_found)}")
        print(f"Subjects found:        {len(subjects_found)}")
        print(f"SOP files found:       {len(sop_files_processed)}")
        print()
        print(f"Redirect rules generated: {total_rules}")
        print(f"  301 redirects:  {len(rules_301)}")
        print(f"  200 rewrites:   {len(rules_200)}")
        print(f"  Static rules:   {len(static_rules)}")
        print()
        print(f"Duplicate URLs:        {len(dup_urls)}")
        print(f"Duplicate destinations:{len(dup_dests)}")
        print(f"Invalid filenames:     {len(invalid_filenames)}")
        print(f"Skipped files:         {skipped_files_count}")
        print()
        print("Completed successfully.")

        return True
