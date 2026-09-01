"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** /ops redirige a la primera vista; la guardia del layout ya validó sesión. */
export default function OpsIndex() {
  const router = useRouter();
  useEffect(() => { router.replace("/ops/usuarios"); }, [router]);
  return null;
}
