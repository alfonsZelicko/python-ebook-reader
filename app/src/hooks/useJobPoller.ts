"use client";

import { useEffect, useRef, useState } from "react";
import { useApolloClient } from "@apollo/client/react";
import { JOB_STATUS_QUERY } from "@/graphql/queries";
import type { JobStatus } from "@/types/graphql";

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 300; // 10 minutes

interface JobStatusData {
  jobStatus: JobStatus;
}

export function useJobPoller(jobId: string | null) {
  const client = useApolloClient();
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const pollCount = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJobStatus(null);
      setIsPolling(false);
      setTimedOut(false);
      pollCount.current = 0;
      return;
    }

    setIsPolling(true);
    setTimedOut(false);
    pollCount.current = 0;

    const stop = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };

    intervalRef.current = setInterval(async () => {
      pollCount.current += 1;

      if (pollCount.current > MAX_POLLS) {
        stop();
        setTimedOut(true);
        return;
      }

      try {
        const { data } = await client.query<JobStatusData>({
          query: JOB_STATUS_QUERY,
          variables: { jobId },
          fetchPolicy: "network-only",
        });

        const status = data?.jobStatus;
        if (status) {
          setJobStatus(status);
          if (status.status === "COMPLETED" || status.status === "FAILED") {
            stop();
          }
        }
      } catch {
        // network errors: keep polling (up to max)
      }
    }, POLL_INTERVAL_MS);

    return stop;
  }, [jobId, client]);

  return { jobStatus, isPolling, timedOut };
}
