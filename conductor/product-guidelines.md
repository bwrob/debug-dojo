# Product Guidelines

## Tone and Voice
The `debug-dojo` project adopts an **Enthusiastic and Gamified** tone. We lean into the "Dojo" and "Zen" themes, utilizing martial arts metaphors and encouraging language to make the technical process of debugging feel like a rewarding journey of mastery. Documentation and user-facing messages should be welcoming, clear, and inspiring.

## Visual Identity and Terminal UX
- **Readability First:** While we embrace a thematic aesthetic, technical clarity is paramount. Visual elements, colors, and styling must enhance the scannability of code and data. We avoid low-contrast combinations or excessive "fluff" that could distract from the debugging task.
- **Thematic Consistency:** We use a consistent color palette and subtle thematic cues (like symbols or structured headers) that reinforce the "Dojo" brand without cluttering the interface.
- **Rich Interaction:** Every user interaction should provide high-fidelity feedback. We leverage `rich` to ensure that data representation is visually structured, making complex objects easy to parse at a glance.
- **Discoverability:** The CLI is designed to be intuitive. Commands and flags must be easy to discover through robust help menus, ensuring that users can focus on their "practice" without getting lost in the tooling.

## Gamification (Dojo Belts)
Our progression system is **Engagement-Based**. While technical mastery is honored, the primary goal of the "Dojo Belts" is to encourage consistent usage and exploration of the tool's features. We want the system to be approachable for beginners, rewarding curiosity and regular practice as much as complex achievements.

## Resilience and Error Handling
- **Graceful Degradation:** The user's debugging flow is sacred. If an enhanced "rich" feature or visual element fails to render, the tool must fall back to standard text output seamlessly. `debug-dojo` should never be the cause of a session crash; it should always remain a reliable companion in the dojo.
