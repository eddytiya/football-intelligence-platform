function FeatureCard({

    number,

    color,

    icon,

    title,

    description

}) {

    return (

        <div
            className="feature-card"
            style={{ "--accent": color }}
        >

            <div className="feature-number">

                {number}

            </div>

            <div className="feature-icon">

                {icon}

            </div>

            <h3>

                {title}

            </h3>

            <p>

                {description}

            </p>

            <button className="feature-btn">

                <span>

                    Explore Feature

                </span>

                <span className="feature-arrow">

                    →

                </span>

            </button>

        </div>

    );

}

export default FeatureCard;