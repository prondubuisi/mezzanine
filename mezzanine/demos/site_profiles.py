"""
IA profiles for public-site clones (structure + original copy only).

Each profile models the *shape* of a well-known site — navigation, page
types, news sections — not trademarks, branding assets, or scraped copy.
"""

from __future__ import annotations

from typing import Any

# Shared field: pages are (title, slug, html); posts are (title, slug, category, html)

PROFILES: dict[str, dict[str, Any]] = {
    "techcrunch": {
        "display_name": "TechCrunch-shaped demo",
        "site_name": "TC Demo",
        "tagline": "Startup and technology news (IA demo)",
        "inspired_by": "https://techcrunch.com/",
        "primary_nav_label": "Latest",
        "pages": [
            (
                "Startups",
                "startups",
                "<p>Coverage of early-stage companies, product launches, and "
                "founder stories — modeled after a tech news startup desk.</p>",
            ),
            (
                "Venture",
                "venture",
                "<p>Funding rounds, VCs, and market maps. In production this "
                "would be a filtered river of posts by category.</p>",
            ),
            (
                "Apps",
                "apps",
                "<p>Mobile and web product news. Nova maps this to pages + "
                "blog categories rather than a custom post type zoo.</p>",
            ),
            (
                "Events",
                "events",
                "<p>Conference and meetup listings. Gap: no first-class Events "
                "model or calendar UI in Y1 Nova.</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by TechCrunch. "
                "Not affiliated with TechCrunch or Yahoo.</p>",
            ),
        ],
        "categories": ["AI", "Startups", "Venture", "Apps", "Security"],
        "posts": [
            (
                "Series A chatter: why vertical SaaS still raises",
                "series-a-vertical-saas",
                "Venture",
                "<p>Sample analysis post for a tech news river.</p>",
            ),
            (
                "On-device models ship to laptops first",
                "on-device-models-laptops",
                "AI",
                "<p>Sample AI desk brief.</p>",
            ),
            (
                "Password managers and the browser wars",
                "password-managers-browser-wars",
                "Security",
                "<p>Sample security short.</p>",
            ),
            (
                "Indie apps find distribution without storefronts",
                "indie-apps-distribution",
                "Apps",
                "<p>Sample apps desk post.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Needs infinite scroll / river homepage, not static index.",
            "Needs topic taxonomy beyond flat BlogCategory.",
            "Needs author bylines and staff pages as first-class entities.",
            "Needs related-posts and most-read modules.",
            "Needs newsletter capture (Form exists; not embedded in chrome).",
        ],
    },
    "time": {
        "display_name": "TIME-shaped demo",
        "site_name": "Time Demo",
        "tagline": "News and ideas (IA demo)",
        "inspired_by": "https://time.com/",
        "primary_nav_label": "Magazine",
        "pages": [
            (
                "Politics",
                "politics",
                "<p>Section landing for politics coverage.</p>",
            ),
            (
                "World",
                "world",
                "<p>Section landing for world news.</p>",
            ),
            (
                "Business",
                "business",
                "<p>Section landing for business and markets.</p>",
            ),
            (
                "Health",
                "health",
                "<p>Section landing for health and science-adjacent coverage.</p>",
            ),
            (
                "Ideas",
                "ideas",
                "<p>Essays and opinion-style section landing.</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by TIME. "
                "Not affiliated with TIME USA, LLC.</p>",
            ),
        ],
        "categories": [
            "Politics",
            "World",
            "Business",
            "Health",
            "Science",
            "Ideas",
            "Entertainment",
        ],
        "posts": [
            (
                "What leaders are watching this week",
                "leaders-watching-this-week",
                "Politics",
                "<p>Sample politics package lede.</p>",
            ),
            (
                "Climate finance after the summit",
                "climate-finance-after-summit",
                "World",
                "<p>Sample world desk analysis.</p>",
            ),
            (
                "Markets digest: rates, jobs, and housing",
                "markets-digest-rates-jobs",
                "Business",
                "<p>Sample business brief.</p>",
            ),
            (
                "An idea worth arguing about",
                "idea-worth-arguing",
                "Ideas",
                "<p>Sample ideas essay stub.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Section landings need post listings filtered by category URL.",
            "Magazine cover / Person of the Year style packages not modeled.",
            "Paywall / subscriber gate not in kernel.",
            "Multimedia (video, photo essays) not first-class.",
            "Newsletter product surface missing.",
        ],
    },
    "whitehouse": {
        "display_name": "White House–style briefing demo",
        "site_name": "The Briefing Room",
        "tagline": "Releases, briefings, and presidential actions (demo)",
        "inspired_by": "https://www.whitehouse.gov/",
        "primary_nav_label": "News",
        # Page slugs match BlogCategory slugs so section landings list posts.
        "pages": [
            (
                "Releases",
                "releases",
                "<p>Official statements and press releases. Items below are "
                "published news posts in the <strong>Releases</strong> category.</p>",
            ),
            (
                "Briefings",
                "briefings",
                "<p>Press briefing notes and remarks. Full live video and "
                "transcript packages are a later enhancement; this demo lists "
                "briefing posts for the section.</p>",
            ),
            (
                "Presidential Actions",
                "presidential-actions",
                "<p>Summaries of executive orders, memoranda, and proclamations. "
                "Structured legal metadata is not modeled yet — posts stand in "
                "for the public index.</p>",
            ),
            (
                "Nominations",
                "nominations",
                "<p>Nominations and appointments announced by the administration.</p>",
            ),
            (
                "Administration",
                "administration",
                "<p>Leadership overview for this demo site. In a production "
                "build this would link to agency and staff pages.</p>"
                "<ul><li>Office of the Press Secretary (demo)</li>"
                "<li>Domestic Policy Council (demo)</li>"
                "<li>National Security Council (demo)</li></ul>",
            ),
            (
                "Priorities",
                "priorities",
                (
                    "<p>Issue hubs used on the home grid:</p><ul>"
                    '<li><a href="/releases/">Economy &amp; infrastructure</a></li>'
                    '<li><a href="/briefings/">Public health briefings</a></li>'
                    '<li><a href="/presidential-actions/">Energy permitting</a></li>'
                    '<li><a href="/nominations/">Personnel nominations</a></li>'
                    "</ul>"
                ),
            ),
            (
                "About",
                "about",
                "<p>This is an <strong>unofficial Nova demo</strong> of an "
                "official-style communications site. Information architecture "
                "is inspired by whitehouse.gov. It is not affiliated with the "
                "U.S. government.</p>"
                "<p>Recreate it with <code>nova-project … --kit whitehouse</code> "
                "then <code>seed_site_clone --site whitehouse</code>.</p>",
            ),
        ],
        "categories": [
            "Releases",
            "Briefings",
            "Presidential Actions",
            "Nominations",
        ],
        "posts": [
            (
                "Statement on infrastructure progress",
                "statement-infrastructure-progress",
                "Releases",
                "<p>The administration today highlighted continued delivery on "
                "infrastructure projects in ports, rail, and broadband, "
                "crediting bipartisan legislation and state partners.</p>"
                "<p><em>Sample release for the Nova White House–style demo.</em></p>",
            ),
            (
                "Fact sheet: manufacturing investment",
                "fact-sheet-manufacturing-investment",
                "Releases",
                "<p>Private-sector manufacturers announced new facilities "
                "supporting supply-chain resilience. This fact sheet summarizes "
                "commitments for press use.</p>",
            ),
            (
                "Press briefing: daily notes",
                "press-briefing-daily-notes",
                "Briefings",
                "<p>Summary notes from today’s press briefing covering "
                "legislative outlook, international calls, and weekend events.</p>"
                "<p>Transcript and video would attach here in a fuller build.</p>",
            ),
            (
                "Remarks on disaster recovery funding",
                "remarks-disaster-recovery-funding",
                "Briefings",
                "<p>Remarks as prepared for delivery on supplemental recovery "
                "funding for communities affected by recent storms.</p>",
            ),
            (
                "Executive action summary: energy permits",
                "executive-action-energy-permits",
                "Presidential Actions",
                "<p>Summary of an executive action directing agencies to "
                "accelerate permitting reviews for critical energy "
                "infrastructure while maintaining environmental standards.</p>",
            ),
            (
                "Memorandum on federal cybersecurity baselines",
                "memorandum-federal-cybersecurity",
                "Presidential Actions",
                "<p>Presidential memorandum establishing baseline cybersecurity "
                "requirements for federal civilian executive branch agencies.</p>",
            ),
            (
                "Nomination: Deputy Secretary of Transportation",
                "nomination-deputy-secretary-transportation",
                "Nominations",
                "<p>The President announced the nomination of a deputy secretary "
                "to the Department of Transportation. Biography and ethics "
                "paperwork would link from a full newsroom package.</p>",
            ),
            (
                "Appointments to the Export Council",
                "appointments-export-council",
                "Nominations",
                "<p>Appointments to the President’s Export Council, representing "
                "labor, small business, and manufacturing stakeholders.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Document types (EO PDF packages) still lightweight — posts stand in.",
            "Live video player not included.",
            "USWDS not vendored; kit tokens approximate official chrome.",
        ],
    },
    "harvard_gazette": {
        "display_name": "Harvard Gazette-shaped demo",
        "site_name": "Gazette Demo",
        "tagline": "University news (IA demo)",
        "inspired_by": "https://news.harvard.edu/gazette/",
        "primary_nav_label": "Campus",
        "pages": [
            (
                "Campus & Community",
                "campus-community",
                "<p>Campus life and community stories section.</p>",
            ),
            (
                "Research",
                "research",
                "<p>Research highlights and faculty work.</p>",
            ),
            (
                "Nation & World",
                "nation-world",
                "<p>University voice on national and global issues.</p>",
            ),
            (
                "Arts & Culture",
                "arts-culture",
                "<p>Arts programming and cultural coverage.</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by the Harvard "
                "Gazette. Not affiliated with Harvard University.</p>",
            ),
        ],
        "categories": [
            "Campus",
            "Research",
            "Nation & World",
            "Arts & Culture",
            "Health",
        ],
        "posts": [
            (
                "Lab finds new clue in materials science",
                "lab-clue-materials-science",
                "Research",
                "<p>Sample research brief with placeholder for faculty byline.</p>",
            ),
            (
                "Commencement week: what to know",
                "commencement-week-what-to-know",
                "Campus",
                "<p>Sample campus logistics story.</p>",
            ),
            (
                "Exhibition opens at the university museum",
                "exhibition-opens-museum",
                "Arts & Culture",
                "<p>Sample arts listing.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Faculty / school taxonomy not in kernel (Institute kit is thin).",
            "Research story templates (lede + experts + related papers) missing.",
            "Photojournalism galleries are optional extra, not wired to posts.",
            "Campus calendar / events missing.",
            "People directory not modeled.",
        ],
    },
    "ted_blog": {
        "display_name": "TED Blog-shaped demo",
        "site_name": "TED Blog Demo",
        "tagline": "Ideas worth spreading — blog IA demo",
        "inspired_by": "https://blog.ted.com/",
        "primary_nav_label": "Ideas",
        "pages": [
            (
                "Talks",
                "talks",
                "<p>Talk discovery would embed video. Gap: no first-class Video "
                "or Talk model with speakers and themes.</p>",
            ),
            (
                "Themes",
                "themes",
                "<p>Curated theme hubs (science, design, social change).</p>",
            ),
            (
                "Conferences",
                "conferences",
                "<p>Event series pages. Gap: recurring conference structure.</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by the TED Blog. "
                "Not affiliated with TED Conferences.</p>",
            ),
        ],
        "categories": ["Science", "Design", "Business", "Global issues", "Technology"],
        "posts": [
            (
                "How a talk becomes a movement",
                "talk-becomes-movement",
                "Global issues",
                "<p>Sample ideas essay linking to a fictional talk.</p>",
            ),
            (
                "Design notes from the stage",
                "design-notes-from-stage",
                "Design",
                "<p>Sample design desk post.</p>",
            ),
            (
                "What we learned about attention",
                "learned-about-attention",
                "Science",
                "<p>Sample science-adjacent post.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Video-first Talk entity missing (speaker, duration, themes, embed).",
            "Playlist / watch-next UX missing.",
            "Transcript + translation workflow missing.",
            "Strong visual theme system beyond CSS tokens.",
            "Community comments moderated at scale — comments off by default.",
        ],
    },
    "spotify_newsroom": {
        "display_name": "Spotify Newsroom-shaped demo",
        "site_name": "Nova Newsroom",
        "tagline": "Company news, product, culture (demo)",
        "inspired_by": "https://newsroom.spotify.com/",
        "primary_nav_label": "News",
        # Page slugs match BlogCategory slugs so section landings list posts.
        "pages": [
            (
                "Company News",
                "company-news",
                "<p>Corporate announcements and company milestones. Items "
                "below are published posts in the <strong>Company News</strong> "
                "category.</p>",
            ),
            (
                "Product & Features",
                "product-features",
                "<p>Product launches, feature narratives, and listening "
                "experience stories for this newsroom demo.</p>",
            ),
            (
                "Culture",
                "culture",
                "<p>Workplace, teams, and culture stories from across the "
                "organization.</p>",
            ),
            (
                "Creators",
                "creators",
                "<p>Stories about artists, podcasters, and the creator "
                "economy — sample posts for press and partners.</p>",
            ),
            (
                "Policy",
                "policy",
                "<p>Trust, safety, and policy updates relevant to creators "
                "and the public.</p>",
            ),
            (
                "For the Press",
                "for-the-press",
                "<p>Media kit overview and journalist contact paths. Full "
                "asset packs and embargo workflows are later enhancements; "
                "use the contact form for demo press inquiries.</p>"
                "<ul>"
                "<li>Brand assets — placeholder (Media library)</li>"
                "<li>Executive bios — placeholder</li>"
                '<li><a href="/contact/">Press contact form</a></li>'
                "</ul>",
            ),
            (
                "About",
                "about",
                "<p>This is an <strong>unofficial Nova demo</strong> of a "
                "corporate newsroom. Information architecture is inspired by "
                "newsroom.spotify.com. It is not affiliated with Spotify AB.</p>"
                "<p>Recreate it with <code>nova-project … --kit spotify</code> "
                "then <code>seed_site_clone --site spotify_newsroom</code>.</p>",
            ),
        ],
        "categories": [
            "Company News",
            "Product & Features",
            "Culture",
            "Creators",
            "Policy",
        ],
        "posts": [
            (
                "Introducing a smarter home listening mode",
                "new-listening-feature",
                "Product & Features",
                "<p>Sample product launch: a new listening mode that adapts "
                "playlists to room activity. Press quotes and screenshots "
                "would attach here in a fuller newsroom package.</p>"
                "<p><em>Original demo copy — not a real product announcement.</em></p>",
            ),
            (
                "Q2 product roadmap themes for creators",
                "q2-product-roadmap-creators",
                "Product & Features",
                "<p>Sample feature narrative covering discovery tools, "
                "analytics improvements, and monetization experiments.</p>",
            ),
            (
                "How our teams build in public",
                "teams-build-in-public",
                "Culture",
                "<p>Sample culture story about engineering blogs, open design "
                "critiques, and cross-team demo days.</p>",
            ),
            (
                "Mentorship circles expand across hubs",
                "mentorship-circles-expand",
                "Culture",
                "<p>Sample workplace story on peer mentorship programs in "
                "design, data, and trust &amp; safety teams.</p>",
            ),
            (
                "Company update: new regional studio partnership",
                "regional-studio-partnership",
                "Company News",
                "<p>Sample company announcement about a partnership to support "
                "emerging creators in two regions. Financial details omitted "
                "in this demo stub.</p>",
            ),
            (
                "Annual transparency report summary",
                "annual-transparency-report",
                "Company News",
                "<p>Sample corporate post summarizing content moderation "
                "metrics and appeals outcomes for the past year.</p>",
            ),
            (
                "Creator fund: what changed this season",
                "creator-fund-season-update",
                "Creators",
                "<p>Sample creators desk post explaining eligibility updates "
                "and payout timelines for a fictional fund.</p>",
            ),
            (
                "Policy update for creators on synthetic media",
                "policy-update-creators",
                "Policy",
                "<p>Sample policy note describing labeling requirements for "
                "AI-assisted audio and how appeals work.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Press kit / brand asset library incomplete (Media is_public helps).",
            "Embargoed drafts + timed multi-channel publish missing.",
            "Locale-specific newsrooms (multi-site exists; UX is raw).",
            "Social card / OG image pipeline not productized.",
            "RSS per category exists partially via blog feeds; needs polish.",
        ],
    },
}


def list_sites() -> list[str]:
    return sorted(PROFILES.keys())


def get_profile(slug: str) -> dict[str, Any]:
    try:
        return PROFILES[slug]
    except KeyError as exc:
        known = ", ".join(list_sites())
        raise KeyError(f"Unknown site {slug!r}. Choose one of: {known}") from exc
