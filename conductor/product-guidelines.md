# Product Guidelines

## 1. Tone and Voice

The **debug-dojo** project adopts an **Enthusiastic and Gamified** tone. We lean into the "Dojo" and "Zen" themes, utilizing martial arts metaphors and encouraging language to make the technical process of debugging feel like a rewarding journey of mastery. It should never be to on the nose and still allow focusing on productivity.

- **Welcoming:** Documentation should be accessible to developers of all levels.
- **Clear:** technical explanations must be precise and jargon-free.
- **Inspiring:** User-facing messages should motivate regular practice and exploration.

## 2. Visual Identity & Terminal UX

- **Readability First:** Technical clarity is paramount. Visual elements, colors, and styling must enhance the scannability of code and data. We avoid low-contrast combinations or excessive "fluff".
- **Thematic Consistency:** We use a consistent color palette and subtle thematic cues (symbols, structured headers) that reinforce the "Dojo" brand without cluttering the interface.
- **Rich Interaction:** Every user interaction should provide high-fidelity feedback. We leverage `rich` and `textual` to ensure that data representation is visually structured.
- **Discoverability:** The CLI is designed to be intuitive. Commands and flags must be easy to discover through robust help menus.

## 3. Gamification (Dojo Belts)

Our progression system is **Engagement-Based**.

- **Encourage Exploration:** The primary goal is to promote consistent usage and exploration of advanced features.
- **Approachability:** The system must be welcoming to beginners, rewarding curiosity and regular practice as much as complex achievements.
- **Honor Mastery:** Higher tiers should reflect a deep understanding of the debugging ecosystem.

## 4. Resilience & Error Handling

- **Graceful Degradation:** The user's debugging flow is sacred. If an enhanced visual element fails to render, the tool must fall back to standard text output seamlessly.
- **Zero Crash Policy:** `debug-dojo` should never be the cause of a session crash. It must remain a reliable companion, even when the target script is failing.
