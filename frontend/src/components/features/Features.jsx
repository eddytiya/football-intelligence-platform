import "./Features.css";

import FeatureCard from "./FeatureCard";

import { GiSoccerBall } from "react-icons/gi";
import { FaChartLine } from "react-icons/fa";
import { HiOutlineChartBar } from "react-icons/hi";
import { TbBrain } from "react-icons/tb";

function Features() {

    const features = [

        {
            
            color: "#22c55e",
            icon: <GiSoccerBall />,
            title: "AI Match Prediction",
            description:
                "Predict football matches using trained Machine Learning models including LightGBM and XGBoost."
        },

        {
            
            color: "#4da3ff",
            icon: <FaChartLine />,
            title: "Dynamic ELO Ratings",
            description:
                "Calculate team strength using dynamic ELO ratings updated after every completed match."
        },

        {
            
            color: "#f59e0b",
            icon: <HiOutlineChartBar />,
            title: "Advanced Analytics",
            description:
                "Analyse team form, momentum, goal statistics, recent performances and match trends."
        },

        {
            
            color: "#b791ff",
            icon: <TbBrain />,
            title: "Explainable AI",
            description:
                "Understand WHY the AI predicted a result using feature importance and probability analysis."
        }

    ];

    return (

        <section className="features">

            <div className="features-container">

                <span className="section-tag">
                    WHY CHOOSE US
                </span>

                <h2>
                    Football Intelligence Platform
                </h2>

                <p>
                    Build accurate football predictions using
                    Machine Learning, ELO Ratings,
                    Team Statistics and Explainable AI.
                </p>

                <div className="features-grid">

                    {features.map((feature) => (

                        <FeatureCard

                            key={feature.number}

                            number={feature.number}

                            color={feature.color}

                            icon={feature.icon}

                            title={feature.title}

                            description={feature.description}

                        />

                    ))}

                </div>

            </div>

        </section>

    );

}

export default Features;
