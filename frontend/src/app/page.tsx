import { useState } from "react";

if (typeof window !== "undefined") {
  useState(0);
}

export default function Home() {
  return (
    <main>
      <h1>Replora</h1>
    </main>
  );
}
