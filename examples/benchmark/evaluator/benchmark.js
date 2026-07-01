import http from "k6/http";
import { check, sleep } from 'k6'
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const messagesDuration = new Trend("messages_duration", true);

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// messages stages total: 80s + 1s + 60s = 141s
export const options = {
  scenarios: {
    messages_load: {
      executor: "ramping-vus",
      startVUs: 10,
      stages: [
        { duration: "30s", target: 10 },
        { duration: "60s", target: 600 },
        { duration: "1s",  target: 10 },
        { duration: "60s", target: 10 },
      ],
      exec: "messagesScenario",
    },
    file_constant: {
      executor: "constant-vus",
      vus: 2,
      duration: "151s",
      exec: "fileScenario",
    },
    // messages_load: {
    //   executor: "constant-vus",
    //   vus: 1,
    //   duration: "11s",
    //   exec: "messagesScenario",
    // },
    // file_constant: {
    //   executor: "constant-vus",
    //   vus: 2,
    //   duration: "11s",
    //   exec: "fileScenario",
    // },
  },
};

export function messagesScenario() {
  const res = http.get(`${BASE_URL}/messages`, {
    tags: { name: "messages" },
    timeout: "6s",
  });

  errorRate.add(res.status !== 200);
  messagesDuration.add(res.timings.duration);
  check(res, { "status is 200": (r) => r.status === 200 });
}

export function fileScenario() {
  const res = http.get(`${BASE_URL}/file`, {
    tags: { name: "file" },
    timeout: "6s",
  });

  check(res, { "status is 200": (r) => r.status === 200 });
}
