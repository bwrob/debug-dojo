#set page(width: auto, height: auto, margin: 0pt)

#box(
  fill: rgb("#1a1a1a"),
  inset: 40pt,
  radius: 20pt,
)[
  #stack(
    dir: ltr,
    spacing: 40pt,
    align(horizon, image("logo/logo_python.png", width: 240pt)),
    align(horizon)[
      #text(size: 200pt, fill: rgb("#FFD700"), weight: "bold")[debug]
      #text(size: 200pt, fill: rgb("#FFFFFF"), weight: "bold")[dojo]
    ]
  )
]