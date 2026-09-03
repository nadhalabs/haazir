import { NextResponse } from 'next/server';
export async function POST() { const r=NextResponse.json({ok:true}); r.cookies.delete('haazir_admin_access'); r.cookies.delete('haazir_admin_refresh'); return r; }
