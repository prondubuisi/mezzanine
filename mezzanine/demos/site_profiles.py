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
        "display_name": "White House-shaped demo",
        "site_name": "WH Demo",
        "tagline": "Official-style briefing site (IA demo)",
        "inspired_by": "https://www.whitehouse.gov/",
        "primary_nav_label": "News",
        "pages": [
            (
                "Briefings & Statements",
                "briefings",
                "<p>Press briefing transcripts and statements would live here. "
                "Gap: no document-type Displayable for PDF/transcript packages.</p>",
            ),
            (
                "Presidential Actions",
                "presidential-actions",
                "<p>Executive orders and memoranda index. Gap: structured legal "
                "document metadata and filters.</p>",
            ),
            (
                "Administration",
                "administration",
                "<p>Leadership and agency links — static pages for Y1.</p>",
            ),
            (
                "Priorities",
                "priorities",
                "<p>Issue area hubs (economy, security, energy).</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by whitehouse.gov. "
                "Unofficial. Not a government site.</p>",
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
                "<p>Sample press release body.</p>",
            ),
            (
                "Press briefing: daily notes",
                "press-briefing-daily-notes",
                "Briefings",
                "<p>Sample briefing summary (not a full transcript UI).</p>",
            ),
            (
                "Executive action summary: energy permits",
                "executive-action-energy-permits",
                "Presidential Actions",
                "<p>Sample action summary card.</p>",
            ),
        ],
        "contact": True,
        "notes": [
            "Needs official document types (EO, proclamation) with filters.",
            "Needs live/media embeds and video briefing player.",
            "Needs accessibility-first gov design system (USWDS) not Bootstrap 3.",
            "Needs multi-language and FOIA-style search.",
            "Staff workflow: review → publish gates beyond draft/status.",
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
        "site_name": "Newsroom Demo",
        "tagline": "Company newsroom (IA demo)",
        "inspired_by": "https://newsroom.spotify.com/",
        "primary_nav_label": "Company",
        "pages": [
            (
                "Company News",
                "company-news",
                "<p>Corporate announcements landing.</p>",
            ),
            (
                "Product & Features",
                "product-features",
                "<p>Product launch narratives.</p>",
            ),
            (
                "Culture",
                "culture",
                "<p>Workplace and culture stories.</p>",
            ),
            (
                "For the Press",
                "for-the-press",
                "<p>Media kit and contact paths for journalists. Gap: asset "
                "kit downloads and embargo workflow.</p>",
            ),
            (
                "About",
                "about",
                "<p>About this <strong>IA demo</strong> inspired by Spotify "
                "Newsroom. Not affiliated with Spotify AB.</p>",
            ),
        ],
        "categories": ["Company", "Product", "Culture", "Creators", "Policy"],
        "posts": [
            (
                "Introducing a new listening feature",
                "new-listening-feature",
                "Product",
                "<p>Sample product launch post.</p>",
            ),
            (
                "How our teams build in public",
                "teams-build-in-public",
                "Culture",
                "<p>Sample culture story.</p>",
            ),
            (
                "Policy update for creators",
                "policy-update-creators",
                "Policy",
                "<p>Sample policy note for press.</p>",
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
