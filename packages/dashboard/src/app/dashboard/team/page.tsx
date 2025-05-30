"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter as _CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Mock team members data
const mockTeamMembers = [
  {
    id: "user-1",
    name: "Alex Johnson",
    email: "alex@example.com",
    role: "admin",
    status: "active",
    avatar: "AJ",
    last_active: "2025-05-27T16:30:00Z",
    joined_at: "2024-11-15T10:00:00Z",
    permissions: ["all"]
  },
  {
    id: "user-2",
    name: "Maria Garcia",
    email: "maria@example.com",
    role: "developer",
    status: "active",
    avatar: "MG",
    last_active: "2025-05-27T15:45:00Z",
    joined_at: "2025-01-20T14:30:00Z",
    permissions: ["credentials:read", "credentials:write", "wallets:read", "wallets:write"]
  },
  {
    id: "user-3",
    name: "Thomas Weber",
    email: "thomas@example.com",
    role: "developer",
    status: "active",
    avatar: "TW",
    last_active: "2025-05-26T17:20:00Z",
    joined_at: "2025-02-10T09:15:00Z",
    permissions: ["credentials:read", "credentials:write", "wallets:read"]
  },
  {
    id: "user-4",
    name: "Sarah Chen",
    email: "sarah@example.com",
    role: "viewer",
    status: "active",
    avatar: "SC",
    last_active: "2025-05-27T12:10:00Z",
    joined_at: "2025-03-05T11:45:00Z",
    permissions: ["credentials:read", "wallets:read", "compliance:read"]
  },
  {
    id: "user-5",
    name: "James Wilson",
    email: "james@example.com",
    role: "developer",
    status: "invited",
    avatar: "JW",
    joined_at: "2025-05-25T13:30:00Z",
    permissions: ["credentials:read", "credentials:write", "wallets:read"]
  }
]

// Roles and their descriptions
const roles = [
  {
    id: "admin",
    name: "Admin",
    description: "Full access to all features and settings"
  },
  {
    id: "developer",
    name: "Developer",
    description: "Access to development features and API"
  },
  {
    id: "viewer",
    name: "Viewer",
    description: "Read-only access to data and analytics"
  }
]

// Available permissions
const availablePermissions = [
  { id: "credentials:read", name: "View Credentials", category: "Credentials" },
  { id: "credentials:write", name: "Manage Credentials", category: "Credentials" },
  { id: "wallets:read", name: "View Wallets", category: "Wallets" },
  { id: "wallets:write", name: "Manage Wallets", category: "Wallets" },
  { id: "compliance:read", name: "View Compliance", category: "Compliance" },
  { id: "compliance:write", name: "Manage Compliance", category: "Compliance" },
  { id: "billing:read", name: "View Billing", category: "Billing" },
  { id: "billing:write", name: "Manage Billing", category: "Billing" },
  { id: "team:read", name: "View Team", category: "Team" },
  { id: "team:write", name: "Manage Team", category: "Team" }
]

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric"
  })
}

function formatRelativeTime(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return `${diffInSeconds} seconds ago`
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)} minutes ago`
  } else if (diffInSeconds < 86400) {
    return `${Math.floor(diffInSeconds / 3600)} hours ago`
  } else {
    return `${Math.floor(diffInSeconds / 86400)} days ago`
  }
}

function getRoleBadge(role: string) {
  switch (role) {
    case "admin":
      return <Badge className="bg-blue-500">Admin</Badge>
    case "developer":
      return <Badge className="bg-green-500">Developer</Badge>
    case "viewer":
      return <Badge className="bg-purple-500">Viewer</Badge>
    default:
      return <Badge>{role}</Badge>
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "active":
      return <Badge variant="outline" className="border-green-500 text-green-600">Active</Badge>
    case "invited":
      return <Badge variant="outline" className="border-yellow-500 text-yellow-600">Invited</Badge>
    case "disabled":
      return <Badge variant="outline" className="border-red-500 text-red-600">Disabled</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

function getAvatarColor(id: string) {
  const colors = [
    "bg-blue-500",
    "bg-green-500",
    "bg-purple-500",
    "bg-orange-500",
    "bg-pink-500",
    "bg-indigo-500"
  ]
  const index = id.charCodeAt(id.length - 1) % colors.length
  return colors[index]
}

export default function TeamPage() {
  const [showInviteDialog, setShowInviteDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedMember, setSelectedMember] = useState<typeof mockTeamMembers[0] | null>(null)
  
  const handleEditMember = (member: typeof mockTeamMembers[0]) => {
    setSelectedMember(member)
    setShowEditDialog(true)
  }
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Team Management</h1>
          <p className="text-muted-foreground">
            Manage team members and their access to EUDI-Connect
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
            <DialogTrigger asChild>
              <Button>Invite Team Member</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Invite Team Member</DialogTitle>
                <DialogDescription>
                  Send an invitation to a new team member to join your EUDI-Connect account.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="email" className="text-right">
                    Email
                  </Label>
                  <Input
                    id="email"
                    className="col-span-3"
                    placeholder="colleague@example.com"
                    type="email"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="role" className="text-right">
                    Role
                  </Label>
                  <Select defaultValue="developer">
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map(role => (
                        <SelectItem key={role.id} value={role.id}>
                          <div>
                            <span>{role.name}</span>
                            <p className="text-xs text-muted-foreground">{role.description}</p>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label className="text-right pt-2">
                    Permissions
                  </Label>
                  <div className="col-span-3 space-y-4">
                    {["Credentials", "Wallets", "Compliance", "Billing", "Team"].map(category => (
                      <div key={category} className="space-y-2">
                        <h4 className="text-sm font-medium">{category}</h4>
                        <div className="space-y-1">
                          {availablePermissions
                            .filter(p => p.category === category)
                            .map(permission => (
                              <div key={permission.id} className="flex items-center gap-2">
                                <input 
                                  type="checkbox" 
                                  id={`invite-${permission.id}`} 
                                  className="h-4 w-4" 
                                  defaultChecked={permission.id.endsWith(":read")}
                                />
                                <Label htmlFor={`invite-${permission.id}`} className="font-normal text-sm">
                                  {permission.name}
                                </Label>
                              </div>
                            ))
                          }
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                  Cancel
                </Button>
                <Button>
                  Send Invitation
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>
            Manage your team members and their access permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50">
                <tr>
                  <th scope="col" className="px-6 py-3">User</th>
                  <th scope="col" className="px-6 py-3">Role</th>
                  <th scope="col" className="px-6 py-3">Status</th>
                  <th scope="col" className="px-6 py-3">Last Active</th>
                  <th scope="col" className="px-6 py-3">Joined</th>
                  <th scope="col" className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {mockTeamMembers.map(member => (
                  <tr key={member.id} className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white ${getAvatarColor(member.id)}`}>
                          {member.avatar}
                        </div>
                        <div>
                          <p className="font-medium">{member.name}</p>
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getRoleBadge(member.role)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(member.status)}
                    </td>
                    <td className="px-6 py-4">
                      {member.last_active ? formatRelativeTime(member.last_active) : "Never"}
                    </td>
                    <td className="px-6 py-4">
                      {formatDateTime(member.joined_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleEditMember(member)}
                        >
                          Edit
                        </Button>
                        {member.status === "invited" ? (
                          <Button variant="outline" size="sm">
                            Resend
                          </Button>
                        ) : member.status === "active" ? (
                          <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                            Disable
                          </Button>
                        ) : (
                          <Button variant="outline" size="sm" className="text-green-600 border-green-200 hover:bg-green-50">
                            Enable
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Team Member</DialogTitle>
            <DialogDescription>
              Update role and permissions for {selectedMember?.name}
            </DialogDescription>
          </DialogHeader>
          {selectedMember && (
            <div className="grid gap-4 py-4">
              <div className="flex items-center gap-3 mb-2">
                <div className={`h-10 w-10 rounded-full flex items-center justify-center text-white ${getAvatarColor(selectedMember.id)}`}>
                  {selectedMember.avatar}
                </div>
                <div>
                  <p className="font-medium">{selectedMember.name}</p>
                  <p className="text-sm text-muted-foreground">{selectedMember.email}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-role" className="text-right">
                  Role
                </Label>
                <Select defaultValue={selectedMember.role}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    {roles.map(role => (
                      <SelectItem key={role.id} value={role.id}>
                        <div>
                          <span>{role.name}</span>
                          <p className="text-xs text-muted-foreground">{role.description}</p>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid grid-cols-4 items-start gap-4">
                <Label className="text-right pt-2">
                  Permissions
                </Label>
                <div className="col-span-3 space-y-4">
                  {["Credentials", "Wallets", "Compliance", "Billing", "Team"].map(category => (
                    <div key={category} className="space-y-2">
                      <h4 className="text-sm font-medium">{category}</h4>
                      <div className="space-y-1">
                        {availablePermissions
                          .filter(p => p.category === category)
                          .map(permission => (
                            <div key={permission.id} className="flex items-center gap-2">
                              <input 
                                type="checkbox" 
                                id={`edit-${permission.id}`} 
                                className="h-4 w-4" 
                                defaultChecked={
                                  selectedMember.permissions.includes("all") || 
                                  selectedMember.permissions.includes(permission.id)
                                }
                                disabled={selectedMember.permissions.includes("all")}
                              />
                              <Label htmlFor={`edit-${permission.id}`} className="font-normal text-sm">
                                {permission.name}
                              </Label>
                            </div>
                          ))
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <Card>
        <CardHeader>
          <CardTitle>Access Control</CardTitle>
          <CardDescription>
            Default access policies for each role
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {roles.map(role => (
              <div key={role.id} className="border rounded-md p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{role.name}</h3>
                    {getRoleBadge(role.id)}
                  </div>
                  <Button variant="outline" size="sm">Edit Default Permissions</Button>
                </div>
                <p className="text-sm text-muted-foreground mb-4">{role.description}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {["Credentials", "Wallets", "Compliance", "Billing", "Team"].map(category => (
                    <div key={category} className="space-y-2">
                      <h4 className="text-sm font-medium">{category}</h4>
                      <div className="space-y-1">
                        {availablePermissions
                          .filter(p => p.category === category)
                          .map(permission => (
                            <div key={permission.id} className="flex items-center gap-2">
                              <div className={`h-2 w-2 rounded-full ${
                                role.id === "admin" || 
                                (role.id === "developer" && !permission.id.includes("billing") && !permission.id.includes("team:write")) ||
                                (role.id === "viewer" && permission.id.endsWith(":read"))
                                  ? "bg-green-500" 
                                  : "bg-gray-300"
                              }`}></div>
                              <span className="text-sm">{permission.name}</span>
                            </div>
                          ))
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
