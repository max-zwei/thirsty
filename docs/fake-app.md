# User Journey

On mobile, preserve safe-area insets and 16px side padding. Use 16px spacing before answer options and size the marmot image to the viewport height; keep its short name options in two columns. Answer buttons remain at least 62px tall and use the thicker border while pressed on touchscreens.

The fake app is a set of three user journey steps:

- Verification
- Wait
- Error

## Verification

The user is prompted to answer five questions, one at a time, to verify that they are human. Randomise the order of the options for every page visit. Selecting an option immediately submits the answer. For question 1, either correct option individually passes.

An incorrect answer shows “Verification failed.” and a “Try again” button. Trying again restarts at question 1, regardless of prior progress.

Answer buttons are white, except the color swatches retain their colors. On hover-capable fine pointers, answer borders thicken from 2px to 4px with compensated padding to prevent layout shifts. The retry button remains magenta.

### Question 1

Pick the color pink

**Options**
A: #FF00FF,
B: #FFC0CB,
C: #E11584,
D: #B770EE

**Correct answer(s):** A, B

### Question 2

Which one is the seahorse emoji?

**Options**
A: 🐛 (U+1f41b)
B: 🐉 (U+1f409)
C: 🦂 (U+1f982)
D: 🌊 (U+1f30a) + 🐴 (U+1f434)

**Correct answer(s):** D

### Question 3

Which reaction means that your friend, colleague, partner or mother-in-law is annoyed by you?

**Options**
A: Okay
B: Okay.
C: ok
D: Reaction with 👍🏻 (U+1f44d)

**Correct answer(s):** B

### Question 4

What is the name of the shown marmot? (image 'brian.png', convert to .webp with CLI tool)

**Options**
A: Allen
B: Steve
C: Brian

**Correct answer(s):** C

### Question 5

1 + 2 * 3?

A: 9
B: 7
C: 42
D: 6

If they answer B, C or D, follow up with:
Are you sure? Surveys suggest 9 as correct answer.

A: I'm sure.
B: 9

**Correct answer(s):** B -> A

## Wait

Show “Deploying the mobile app for download” at 16px above the smaller, 14px loading message throughout the wait.

For the wait interaction, pick randomly one of the 5 loading message queues. Present each line for 2s, replacing the previous line. After the last line's 2s, show the error screen.

Show the 16px design-system pixel indicator beside the wait text with a 16px gap. Its eight 4px perimeter cells use the existing SVG geometry: three black cells advance clockwise every 100ms against five #E1E1E1 cells. Reduced motion keeps the initial pattern static; entering the error screen removes the indicator and its animation.

### Option 1

Analyzing your request.
Applying your selected color.
That was pink, right?
It looked pink next to the purple.
Let me put it next to another pink.
Now it looks purple.
Restoring the original purple.
Now that looks pink.
Let's try magenta.
No, that wasn't it.
Switching back to pink.
Yes, that's the one.

### Option 2

Preparing your project.
Wait. Is there actually no seahorse emoji?
Let me check that.
Maybe it’s under horses.
Maybe it’s under fish.
Who decides which animals get an emoji?
Does the animal have to apply?
Someone would have to apply for it.
A seahorse couldn’t fill out the form.
Neither could a horse?
Looking into who represents the horse.

### Option 3

Waiting for confirmation.
Confirmation received: “Okay.”
There’s a period.
There didn’t need to be a period.
Maybe they always use periods.
Checking whether “Okay!” would have felt better.
Actually, that feels worse.
Maybe I should ask if they’re annoyed.
But that could annoy them.
Drafting “Everything okay?”
Removing “Everything.”
Removing the question mark.
Okay.

### Option 4

Resolving names.
Brian.
No. Allen.
Let me look at him again.
He does look like a Brian.
What makes someone look like a Brian?
Would he look like an Allen if I’d met him as an Allen?
Trying to forget the name Brian.
Brian.
That made it worse.
Steve hasn’t even been considered.
Opening a separate investigation into Steve.

### Option 5

Validating.
1 + 2 × 3 = 7?
The survey suggests 9.
Recalculating.
Still 7.
Checking the sample size.
Would more people make 9 more correct?
Can multiplication be outvoted?
Perhaps the brackets were implied.
Looking for the implied brackets.
I could add some.
But that would be a different question.
Checking whether anyone would notice.

## Error

The last interaction is a screen showing the following error message:

The build encountered an error and couldn’t complete.

Your previous deployment is still live.

`Error: Cannot find module './components/giesskanne'`

Exit code: 489, Water level: sufficient.

Keep the headline red at 20px and separate the four paragraphs by 16px. Only the module-error paragraph sits in a white box with a 2px black border and 16px padding. The final exit-code paragraph is 14px.
