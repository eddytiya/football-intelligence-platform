import { useEffect, useState } from "react";

import { getCompetitions } from "../api/competitionApi";


function useCompetitions() {

    const [
        competitions,
        setCompetitions,
    ] = useState([]);

    const [
        loading,
        setLoading,
    ] = useState(true);

    const [
        error,
        setError,
    ] = useState(null);

    useEffect(() => {

        const fetchCompetitions = async () => {

            try {

                const data =
                    await getCompetitions();

                setCompetitions(data);

            } catch (err) {

                setError(err);

            } finally {

                setLoading(false);

            }

        };

        fetchCompetitions();

    }, []);

    return {

        competitions,

        loading,

        error,

    };

}

export default useCompetitions;