# Crumble

A scroll-film landing page and brand videos for Crumble Pakistan (cookies, ice cream cookies, shakes and Crumble Cold).

## The website
`index.html` is a single self-contained page (GSAP, ScrollTrigger and Lenis from CDN).

```bash
python3 -m http.server 5180
```
Then open http://localhost:5180.

- A scroll film built from real product cutouts (`assets/film/`): the cookie breaks, soft-serve rises,
  then shakes, Crumble Cold and the cookies, with colour waves between chapters.
- Sections: Signatures showcase, Inside a Crumble, full menu with real prices, packaging, Crumble Pot,
  cities and ordering.
- Responsive from 360 px phones to 2560 px displays, with a mobile menu and reduced-motion support.

## Videos
- `video/crumble-brand-film.mp4`: 31 s brand film (HyperFrames project in `video/brand/`).
- `video/crumble-website-walkthrough.mp4`: 50 s, 60 fps walkthrough of the site.

Render the brand film again from `video/brand/` with the HyperFrames CLI (`npx hyperframes render`).

## Credits
Music and sound-effect credits (the music is CC BY 3.0 and must be credited) are in `video/CREDITS.md`.
