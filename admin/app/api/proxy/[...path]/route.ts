import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';
const api = process.env.BACKEND_API_URL;
async function forward(req:NextRequest, ctx:{params:Promise<{path:string[]}>}) {
  if (!api) return NextResponse.json({detail:'Server API is not configured'}, {status:503});
  const token=(await cookies()).get('haazir_admin_access')?.value;
  if (!token) return NextResponse.json({detail:'Session expired'}, {status:401});
  const {path}=await ctx.params; const target=new URL(`${api}/${path.join('/')}`); req.nextUrl.searchParams.forEach((v,k)=>target.searchParams.append(k,v));
  const body=['GET','HEAD'].includes(req.method)?undefined:await req.text();
  const upstream=await fetch(target,{method:req.method,headers:{authorization:`Bearer ${token}`,'content-type':'application/json'},body,cache:'no-store'});
  const text=await upstream.text(); const response=new NextResponse(text,{status:upstream.status,headers:{'content-type':upstream.headers.get('content-type')||'application/json'}});
  if (upstream.status===401||upstream.status===403) { response.cookies.delete('haazir_admin_access'); response.cookies.delete('haazir_admin_refresh'); }
  return response;
}
export const GET=forward; export const POST=forward; export const PATCH=forward;
