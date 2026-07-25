# SentientBMS: Hackathon Pitch & Demo Script

## 1. The 30-Second Pitch
"We built **SentientBMS**, an autonomous building energy management system that combines agentic LLM planning with a Model Context Protocol interface and an active Sandbox Digital Twin. Unlike standard rule-based schedules or uninterpretable black-box ML, SentientBMS generates multiple operational hypotheses, simulates their performance in a fast state-space sandbox to compute energy, carbon, and comfort outcomes, and executes the safest, highest-performing strategy. On a peak summer day, SentientBMS achieved **17.3% energy savings** and **17.8% carbon reduction** while preserving comfort."

---

## 2. The 2-Minute Pitch
"Good morning, judges. Buildings consume nearly 40% of global energy, yet most Building Management Systems rely on static, rule-based schedules designed decades ago. They can't adapt to dynamic weather, occupancy, or carbon grid conditions. 

To solve this, we created **SentientBMS**. 

SentientBMS is an autonomous building controller that uses an open-source LLM, the Model Context Protocol, and a digital twin simulator to run closed-loop optimization. 

Here is what makes us unique: **The Symbiotic Digital Twin Sandbox**. 

Instead of letting an AI agent blindly guess HVAC setpoints, SentientBMS functions as a strategic planner. Every 15 minutes, it proposes three candidates: an Eco-Optimized strategy, a Comfort-First strategy, and a Carbon-Aware strategy. 

It passes these to an internal Digital Twin emulator which fast-forwards the simulation for the next 2 hours. A dynamic evaluator calculates the exact impact of each strategy on energy cost, occupant comfort, and carbon emissions. 

The AI agent selects the best option, explains its decision in plain English to the facility manager, and routes it through a deterministic **Safety Gate** that guarantees physical bounds are never violated. 

In our test runs, SentientBMS automatically pre-cooled the building when the grid was clean and occupancy was low, and relaxed cooling during high-carbon grid spikes. The result? 17.3% energy savings and 17.8% carbon reduction. SentientBMS represents the future of safe, autonomous, and explainable smart buildings."

---

## 3. The 5-Minute Demo Script

* **[0:00 - 1:00] Introduction & Setup**
  * Presenter: "Welcome to SentientBMS. Here is our dashboard showing a live 3-zone commercial building."
  * Show: The Streamlit dashboard loaded with baseline data. Point out Zone 1 (Open Office), Zone 2 (Meeting Room), Zone 3 (Executive Suite).
  * Presenter: "We are simulating a hot summer day. Currently, the baseline controller is running static setpoints, leading to high cooling costs and no sensitivity to grid carbon peaks."

* **[1:00 - 2:00] Activating SentientBMS**
  * Presenter: "Now we activate SentientBMS Autonomous Mode. Watch the dynamic charts adapt."
  * Action: Click the "⚡ Re-Run Simulation with New Weights" or show the AI logs populating.
  * Presenter: "The AI agent has started observing the building. It proposes three strategies, simulates them in the Digital Twin Sandbox, and applies the optimal action."

* **[2:00 - 3:30] Scenario Walkthrough**
  * Show: The AI Log.
  * Presenter: "Look at the log at 10:00 AM. The meeting room becomes occupied. SentientBMS selects the Comfort-First strategy to ensure occupants are comfortable. But look at 1:00 PM. The grid carbon intensity spikes. SentientBMS automatically pivots to the Carbon-Aware strategy, shifting load to protect carbon emissions. At 6:00 PM, occupancy drops to zero. The system switches to Eco-Optimized, relaxing setpoints to save energy."

* **[3:30 - 4:15] Safety Gate Demonstration**
  * Presenter: "Reliability is key. What if the agent proposes an unsafe cooling setpoint like 12°C? Our Safety Validator intercepts the command, logs a rejection, and falls back to a safe backup temperature. The building never overheats or freezes."

* **[4:15 - 5:00] Performance Summary & ROI**
  * Presenter: "Let's look at the bottom line. SentientBMS reduced energy usage by 17.3% and carbon emissions by 17.8% compared to the baseline, while keeping comfort penalties to a minimum. SentientBMS is reliable, explainable, and ready to deploy."
