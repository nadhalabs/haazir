import { NextResponse } from 'next/server';
const api = process.env.BACKEND_API_URL;
export async function POST(request: Request) {
  if (!api) return NextResponse.json({detail:'Server API is not configured'}, {status:503});
  const body = await request.text();
  const auth = await fetch(`${api}/auth/login`, {method:'POST', headers:{'content-type':'application/json'}, body, cache:'no-store'});
  const data = await auth.json().catch(()=>({detail:'Authentication failed'}));
  if (!auth.ok) return NextResponse.json(data, {status:auth.status});
  const me = await fetch(`${api}/auth/me`, {headers:{authorization:`Bearer ${data.access_token}`}, cache:'no-store'});
  const user = await me.json().catch(()=>null);
  if (!me.ok || user?.role !== 'ADMIN' || !user?.is_active || user?.is_suspended) return NextResponse.json({detail:'Admin access required'}, {status:403});
  const response = NextResponse.json({user});
  response.cookies.set('haazir_admin_access', data.access_token, {httpOnly:true, secure:process.env.NODE_ENV==='production', sameSite:'strict', path:'/', maxAge:86400});
  response.cookies.set('haazir_admin_refresh', data.refresh_token, {httpOnly:true, secure:process.env.NODE_ENV==='production', sameSite:'strict', path:'/', maxAge:2592000});
  return response;
}
